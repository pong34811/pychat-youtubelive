import socket
import threading
import webbrowser

CLIENT_ID = "dezbvkl619rp5g83gyezee3itn3alg"
SCOPE = "chat:read"
REDIRECT_URI = "http://localhost"


def get_oauth_token() -> str | None:
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=token"
        f"&scope={SCOPE}"
        f"&force_verify=true"
    )

    token = None
    event = threading.Event()

    def _server():
        nonlocal token
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 80))
            server.listen(1)
            server.settimeout(120)
            conn, _ = server.accept()
            data = conn.recv(4096).decode()
            if "access_token=" in data:
                fragment = data.split("access_token=")[1].split("&")[0]
                token = fragment
            conn.send(b"HTTP/1.1 200 OK\r\n\r\nDone, close this window.")
            conn.close()
        except OSError:
            pass
        finally:
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

    return token or None
