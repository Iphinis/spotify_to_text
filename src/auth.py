"""
Handles OAuth authorization code flow and refresh token flow.
Provides helpers to start a local HTTP server and exchange codes for tokens.
"""
import webbrowser
import threading
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import requests

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPE = "playlist-read-private playlist-read-collaborative"


class OAuthHandler(BaseHTTPRequestHandler):
    """Tiny HTTP handler to capture the OAuth redirect with code."""
    server_version = "OAuthHandler/0.1"
    auth_code = None
    error = None

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if 'error' in qs:
            OAuthHandler.error = qs.get('error', [''])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization failed. You can close this window.")
            return
        if 'code' in qs:
            OAuthHandler.auth_code = qs['code'][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization successful. You can close this window.")
            return
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b"Bad request")


def start_local_http_server(redirect_uri, timeout=300):
    """Start an HTTP server to listen for the OAuth redirect. Returns the server object."""
    parsed = urlparse(redirect_uri)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8888
    path = parsed.path or "/callback"
    server = HTTPServer((host, port), OAuthHandler)
    server.expected_path = path
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def authorization_code_flow(client_id, client_secret, redirect_uri):
    """Perform Authorization Code Flow: open browser, capture code, exchange for tokens.
    Returns the token response (dict) on success.
    """
    server = start_local_http_server(redirect_uri)
    auth_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPE,
        "show_dialog": "true"
    }
    auth_url = f"{SPOTIFY_AUTH_URL}?{urlencode(auth_params)}"
    print("Opening browser for Spotify authorization...")
    webbrowser.open(auth_url)
    print("Waiting for authorization... (check opened browser window)")
    for _ in range(600):
        if OAuthHandler.auth_code:
            code = OAuthHandler.auth_code
            break
        if OAuthHandler.error:
            server.shutdown()
            raise RuntimeError(f"Authorization error: {OAuthHandler.error}")
        time.sleep(0.5)
    else:
        server.shutdown()
        raise TimeoutError("No authorization code received in time.")
    server.shutdown()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    resp = requests.post(SPOTIFY_TOKEN_URL, data=data, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Token exchange failed: {resp.status_code} {resp.text}")
    return resp.json()


def refresh_token_flow(client_id, client_secret, refresh_token):
    """Exchange a refresh token for a fresh access token."""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    resp = requests.post(SPOTIFY_TOKEN_URL, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()
