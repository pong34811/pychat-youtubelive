import json
import os
import socket
import threading
import webbrowser
from pathlib import Path


CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID", "dezbvkl619rp5g83gyezee3itn3alg")
SCOPE = "chat:read"
TOKEN_FILE = Path(os.environ.get("APPDATA", ".")) / "pychat-youtubelive" / "twitch_token.json"


CALLBACK_HTML = b"""\
HTTP/1.1 200 OK\r\n\
Content-Type: text/html\r\n\
\r\n\
<!DOCTYPE html>
<html>
<body>
<script>
var h = window.location.hash.substring(1);
if (h) {
  window.location.href = "/?" + h;
} else {
  document.write("No token found. Close this window.");
}
</script>
</body>
</html>"""


TOKEN_OK_HTML = b"HTTP/1.1 200 OK\r\n\r\nDone, close this window."


def _save_token(token: str) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps({"access_token": token, "scope": SCOPE}))


def _load_token() -> str | None:
    try:
        data = json.loads(TOKEN_FILE.read_text())
        if data.get("scope") == SCOPE:
            return data["access_token"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return None


def get_oauth_token() -> str | None:
    saved = _load_token()
    if saved:
        return saved

    # Use high port to avoid requiring admin privileges on port 80
    port = int(os.environ.get("TWITCH_OAUTH_PORT", "18932"))
    redirect_uri = f"http://localhost:{port}"

    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=token"
        f"&scope={SCOPE}"
        f"&force_verify=true"
    )

    token: str | None = None
    event = threading.Event()

    def _server():
        nonlocal token
        server = None
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", port))
            server.listen(1)
            server.settimeout(120)
            conn, _ = server.accept()
            data = conn.recv(4096).decode(errors="ignore")

            if "access_token=" in data:
                token = data.split("access_token=")[1].split("&")[0].split(" ")[0]
                conn.send(TOKEN_OK_HTML)
                if token:
                    _save_token(token)
            else:
                conn.send(CALLBACK_HTML)
                # second request after JS redirect
                conn.close()
                conn, _ = server.accept()
                data = conn.recv(4096).decode(errors="ignore")
                if "access_token=" in data:
                    token = data.split("access_token=")[1].split("&")[0].split(" ")[0]
                    if token:
                        _save_token(token)
                conn.send(TOKEN_OK_HTML)

            conn.close()
        except OSError:
            pass
        finally:
            if server:
                server.close()
            event.set()

    t = threading.Thread(target=_server, daemon=True)
    t.start()
    webbrowser.open(auth_url)
    event.wait(timeout=120)

    if not token:
        print("ไม่ได้รับ token อัตโนมัติ")
        print(f"ลองเปิดลิงก์นี้ใน browser แล้ว authorize:")
        print(auth_url)
        print("หลังจาก authorize แล้ว browser จะ redirect ไป localhost")
        print("ให้ copy access_token จาก URL แล้ว paste ที่นี่:")
        token = input("access_token: ").strip()
        if token:
            _save_token(token)

    return token or None
