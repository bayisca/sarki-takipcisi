import requests
import json
import os

SPOTIFY_CLIENT_ID = os.environ["6f84402ff4b843739327b90bcb98eb2e"]
SPOTIFY_CLIENT_SECRET = os.environ["9c6dd6e4a9264b8ca4c876d8074ec823"]
SPOTIFY_REFRESH_TOKEN = os.environ["BQABEFhB5uRpnL74MCQnXU_hIMMhzUd5ZsI4otjE-u_EDQEhjep53iTl2CAvVb7I38Q56SHKTNKZWUoKMOwk9I_ITjz_yXcLDpLcOqeo4pLBFYtnI6bSJiLhVI0LfwVPm6XimeSEtbNoA5gSo09fQaS1jvh810NvVB3BB1pf1cRmrsgvcbQ6joNEHl0kgP1wHURbhUrXsOD_Q-figHLfI4aOZW-dHunTIkQQ8U2oUfnOgcHom5bzjoq3Hdm2oBfA"]
TELEGRAM_TOKEN = os.environ["8944473175:AAFszcnY1lIfmIrgisjPvYvyKxSEz-2f8aQ"]
TELEGRAM_CHAT_ID = os.environ["1366615695"]

STATE_FILE = "state.json"

def get_access_token():
    resp = requests.post("https://accounts.spotify.com/api/token", data={
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    })
    return resp.json()["access_token"]

def get_followed_artists(token):
    artists = []
    url = "https://api.spotify.com/v1/me/following?type=artist&limit=50"
    headers = {"Authorization": f"Bearer {token}"}
    while url:
        resp = requests.get(url, headers=headers).json()
        artists.extend(resp["artists"]["items"])
        url = resp["artists"]["next"]
    return artists

def get_latest_release(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    params = {"include_groups": "single,album", "limit": 1, "market": "TR"}
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, params=params).json()
    items = resp.get("items", [])
    if not items:
        return None
    return items[0]  # en yeni (Spotify tarihe gore siraliyor)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def main():
    token = get_access_token()
    state = load_state()
    artists = get_followed_artists(token)

    for artist in artists:
        artist_id = artist["id"]
        artist_name = artist["name"]
        release = get_latest_release(token, artist_id)
        if not release:
            continue

        release_id = release["id"]
        last_known = state.get(artist_id)

        if last_known != release_id:
            # ilk calistirmada spam olmasin diye, sadece state bosken bildirim atma
            if last_known is not None:
                msg = f"🎵 {artist_name} yeni bir sarki cikardi: {release['name']}\n{release['external_urls']['spotify']}"
                send_telegram(msg)
            state[artist_id] = release_id

    save_state(state)

if __name__ == "__main__":
    main()