import queue
import re
import socket

from fix_message import sanitize_message
from .base_worker import BaseWorker
from .twitch_auth import get_oauth_token


PLATFORM = "TW"
IRC_HOST = "irc.chat.twitch.tv"
IRC_PORT = 6667
MESSAGE_PATTERN = re.compile(r":(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)")


class TwitchWorker(BaseWorker):
    def __init__(self, channel: str, message_queue: queue.Queue) -> None:
        super().__init__(message_queue)
        self.channel = channel.strip("#").lower()

    def _run(self) -> None:
        token = get_oauth_token()
        if not token:
            self.message_queue.put((PLATFORM, "[ระบบ]", "❌ Twitch: ไม่ได้รับ token"))
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((IRC_HOST, IRC_PORT))
            sock.send(f"PASS oauth:{token}\r\n".encode())
            sock.send(f"NICK {self.channel}\r\n".encode())
            sock.send(f"JOIN #{self.channel}\r\n".encode())
            sock.settimeout(1)
        except Exception as e:
            self.message_queue.put((PLATFORM, "[ระบบ]", f"❌ Twitch: {e}"))
            return

        self.message_queue.put((PLATFORM, "[ระบบ]", f"✅ Twitch: joined #{self.channel}"))

        while not self._stop_event.is_set():
            try:
                data = sock.recv(2048).decode(errors="ignore")
            except socket.timeout:
                continue
            except Exception as e:
                self.message_queue.put((PLATFORM, "[ระบบ]", f"❌ Twitch: {e}"))
                break

            for line in data.split("\r\n"):
                if line.startswith("PING"):
                    sock.send(line.replace("PING", "PONG").encode() + b"\r\n")
                    continue
                match = MESSAGE_PATTERN.match(line)
                if match:
                    name, text = match.group(1), match.group(2)
                    clean = sanitize_message(text)
                    if clean:
                        self.message_queue.put((PLATFORM, name, clean))

        sock.close()
