import os
import requests
import urllib.parse
import webbrowser
import http.server
import socketserver

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
SCOPE = "user-follow-read"

if not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit(
        "Spotify kimlik bilgileri eksik. Lütfen SPOTIFY_CLIENT_ID ve SPOTIFY_CLIENT_SECRET ortam değişkenlerini tanımlayın."
    )

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