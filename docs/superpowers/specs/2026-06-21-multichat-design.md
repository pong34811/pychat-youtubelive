# Multi-Chat (YouTube + TikTok + Twitch) Design

## Goal
เพิ่มความสามารถให้ GUI รองรับการอ่านแชตจาก 3 พร้อมกัน — YouTube, TikTok, Twitch — แสดงรวมในหน้าต่างเดียว

## Architecture

```
gui.py
├── chat_workers/
│   ├── youtube_worker.py    # pytchat (sync, thread)
│   ├── tiktok_worker.py     # TikTokLiveClient (async, thread)
│   └── twitch_worker.py     # IRC + Twitch API (sync, thread)
│
├── tts_handler.py           # TTS (คงเดิม)
├── fix_message.py           # sanitize (คงเดิม)
└── shared_queue             # queue.Queue รวมทุก platform
```

## Data Flow

```
YouTube worker ─┐
TikTok worker  ─┤
Twitch worker  ─┤
                ▼
        shared_queue.put((platform, name, text))
                │
        GUI poll every 100ms
                │
                ▼
        display_message("[YT] name: text")
        display_message("[TT] name: text")
        display_message("[TW] name: text")
        TTS ถ้าเปิด
```

## Platform Details

### YouTube Worker (`youtube_worker.py`)
- ใช้ `pytchat` เหมือนเดิม
- รับ `video_id`
- รันใน thread, sync

### TikTok Worker (`tiktok_worker.py`)
- ใช้ `TikTokLiveClient`
- รับ `username` (ไม่ต้องมี @)
- เป็น async library → ใช้ `asyncio.run()` ใน thread
- Event: `on_comment` → ส่งชื่อ + ข้อความเข้า queue

### Twitch Worker (`twitch_worker.py`)
- ใช้ raw IRC (socket) — ไม่ต้องใช้ twitchio ลด dependency
- รับ `channel_name` + `oauth_token`
- token ได้จาก OAuth PKCE flow:
  ```python
  # เปิด browser ให้ user authorize
  # localhost callback รับ token
  ```

## GUI Changes

### Input section

```
┌────────────────────────────────────────────────────┐
│  YouTube URL: [___________________________]  [▶]   │
│  TikTok  @:   [___________________________]  [▶]   │
│  Twitch  #:   [___________________________]  [▶]   │
├────────────────────────────────────────────────────┤
│  🔊 TTS [✓]  Volume [===●=====]  50%              │
├────────────────────────────────────────────────────┤
│  [YT] John: สวัสดีครับ                              │
│  [TT] user1: hello                                 │
│  [TW] viewer1: lol                                 │
│  ↑ scrollable chat                                 │
├────────────────────────────────────────────────────┤
│  ✅ YouTube: กำลังเชื่อมต่อ | TikTok: กำลังเชื่อมต่อ   │
└────────────────────────────────────────────────────┘
```

### Status
- แต่ละ platform มี status แยก: กำลังเชื่อมต่อ, กำลังอ่าน, error
- แสดงใน status bar หรือ indicator

## Twitch OAuth Flow
1. เปิด browser: `https://id.twitch.tv/oauth2/authorize?client_id=xxx&redirect_uri=http://localhost&response_type=token&scope=chat:read&force_verify=true`
2. User กด authorize
3. Browser redirect ไป `http://localhost/#access_token=xxxx`
4. ในโค้ด: start server บน localhost:80 เพื่อรับ callback หรือให้ user copy token มา paste

## File Changes
| File | Change |
|------|--------|
| `gui.py` | เพิ่ม input 3 platform, status แยก, display prefix |
| `chat_workers/youtube_worker.py` | new — ย้าย logic chat loop จาก gui.py |
| `chat_workers/tiktok_worker.py` | new — TikTokLiveClient wrapper |
| `chat_workers/twitch_worker.py` | new — IRC socket + token management |
| `chat_workers/__init__.py` | new |
| `requirements.txt` | add TikTokLive |

## Not Changing
- `tts_handler.py` — ไม่ต้องแก้
- `fix_message.py` — ไม่ต้องแก้
- `main.py` — CLI คงเดิม
