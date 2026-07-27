import os
import requests
import urllib.parse
import webbrowser
import http.server
import socketserver


def load_dotenv(path):
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def require_setting(name, prompt_text):
    value = os.environ.get(name)
    if value:
        return value

    value = input(f"{prompt_text}: ").strip()
    if not value:
        raise SystemExit(f"{name} tanımlanmadı. İşlemi tekrar başlatın.")

    os.environ[name] = value
    return value


CLIENT_ID = require_setting("SPOTIFY_CLIENT_ID", "Spotify Client ID girin")
CLIENT_SECRET = require_setting("SPOTIFY_CLIENT_SECRET", "Spotify Client Secret girin")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
SCOPE = "user-follow-read"

# 1. Kullanıcıyı yetkilendirme sayfasına yönlendir
auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
    "client_id": CLIENT_ID,
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
})
webbrowser.open(auth_url)

# 2. Callback'i yakalamak için mini bir local server
auth_code = {}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        auth_code["code"] = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Basarili, bu pencereyi kapatabilirsin.")

with socketserver.TCPServer(("127.0.0.1", 8888), Handler) as httpd:
    httpd.handle_request()  # tek bir istek al, kapan

code = auth_code["code"]

if not code:
    raise SystemExit("Spotify yetkilendirme kodu alınamadı. İşlemi tekrar deneyin.")

# 3. Code'u refresh_token ile degistir
resp = requests.post("https://accounts.spotify.com/api/token", data={
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": REDIRECT_URI,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
})
print(resp.json())