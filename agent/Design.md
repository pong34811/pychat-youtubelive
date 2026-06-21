# TTS (Text-to-Speech) Feature Design

## Goal
ให้โปรแกรมอ่านข้อความแชต YouTube Live ออกเสียงแบบเรียลไทม์ ด้วยเสียงภาษาไทยคุณภาพสูง

## Approach
ใช้ **edge-tts** — เรียก Microsoft Edge TTS API (th-TH-PremmawadeeNeural) ไม่ต้องใช้ API key, เสียงไทยเป็นธรรมชาติ

## Architecture

```
main.py                 # คงเดิม, แค่เรียก TTS หลัง print
├── fix_message.py      # คงเดิม
└── tts_handler.py      # NEW: TTS engine + queue management
```

## Data Flow

```
sync_items()
    │
    ▼
sanitize_message() → ถ้าไม่ว่าง
    │
    ├── print(f"{name}: {clean}")
    └── tts_queue.put((name, clean))
            │
            ▼
    TTS background thread:
    while True:
        name, text = queue.get()
        text = re.sub(emoji_pattern, '', text)  # 过滤 emoji ก่อนพูด
        if len(text.strip()) < 2:
            continue
        await edge_tts.Communicate(f"{name} กล่าวว่า {text}").save("temp.mp3")
        play temp.mp3
```

## Components

### tts_handler.py

```python
class TTSHandler:
    def __init__(self, voice: str = "th-TH-PremmawadeeNeural"):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.voice = voice

    def start(self): self.thread.start()

    def speak(self, name: str, message: str):
        self.queue.put((name, message))

    def _run(self):
        # async loop: consume queue, call edge-tts, play audio
```

### Key Behaviors
- **Non-blocking**: main loop ไม่ต้องรอ TTS พูดเสร็จ
- **Sequential**: ข้อความต่อคิวกัน ไม่พูดซ้อน
- **Error resilience**: TTS ล้มเหลว → print warning + continue
- **Filter**: emoji, ข้อความสั้น (< 2 chars) ไม่พูด

## Edge Cases
- ไม่มี internet → TTS fail, print warning, chat loop ทำงานปกติ
- ข้อความยาวมาก → ตัดที่ ~200 ตัวอักษร
- ข้อความซ้ำเร็ว → queue ทำให้พูดต่อเนื่องไม่ตกหล่น
- ไม่มีเสียง (no speaker/headphone) → ไม่กระทบ chat

## Files Changed
| File | Change |
|------|--------|
| `main.py` | import TTSHandler, start thread, call `tts.speak()` หลัง print |
| `tts_handler.py` | new file |
| `requirements.txt` | add `edge-tts` |

## Testing
- ใช้ pytest ทดสอบ `tts_handler.py` โดย mock edge-tts
- ทดสอบ filter logic (emoji filter, length filter)
- ทดสอบ queue behavior (multiple messages)
