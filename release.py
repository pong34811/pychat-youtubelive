import subprocess
import httpx
import os

# Try to get token from git credential manager
proc = subprocess.run(
    ["git", "credential", "fill"],
    input="protocol=https\nhost=github.com\n",
    capture_output=True,
    text=True,
)
cred = {}
for line in proc.stdout.strip().split("\n"):
    if "=" in line:
        key, val = line.split("=", 1)
        cred[key] = val

token = cred.get("password") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

if not token:
    print("No token found. Create one at: https://github.com/settings/tokens")
    print("Then run: $env:GH_TOKEN='your_token'")
    exit(1)

headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

# Check if release already exists
r = httpx.get(
    "https://api.github.com/repos/pong34811/pychat-youtubelive/releases/tags/v1.0.0",
    headers=headers,
)
if r.status_code == 200:
    release = r.json()
    print(f"Release already exists: {release['html_url']}")
else:
    r = httpx.post(
        "https://api.github.com/repos/pong34811/pychat-youtubelive/releases",
        headers=headers,
        json={
            "tag_name": "v1.0.0",
            "name": "v1.0.0",
            "body": "PyChat YouTube Live - GUI with TTS and emoji filter",
        },
    )
    r.raise_for_status()
    release = r.json()
    print(f"Release created: {release['html_url']}")

upload_url = release["upload_url"].replace("{?name,label}", "?name=youtube-tts.exe")
print("Uploading asset...")
with open("dist/youtube-tts.exe", "rb") as f:
    r2 = httpx.post(
        upload_url,
        headers={**headers, "Content-Type": "application/octet-stream"},
        content=f,
    )
r2.raise_for_status()
print("Asset uploaded successfully!")
