# GUI Feature Design

## Goal
เปลี่ยน CLI YouTube Live chat reader เป็น GUI application ด้วย customtkinter มีหน้าต่างโปรแกรมสวยงาม จัดการง่ายขึ้น

## Approach
ใช้ **customtkinter** — สร้าง GUI แบบ modern บน Windows, lightweight, เข้ากับ threading + queue architecture เดิม

## Architecture

```
gui.py                  # NEW: GUI main window (customtkinter)
main.py                 # CLI คงเดิม, แยกจาก GUI
├── fix_message.py      # คงเดิม
└── tts_handler.py      # คงเดิม
```

## Layout

```
┌─────────────────────────────────────────────┐
│  PyChat YouTube Live                         │
├─────────────────────────────────────────────┤
│  [🔗 URL...                          ]      │
│  [▶ Start]  [⏹ Stop]  🔊 TTS [✓]          │
├─────────────────────────────────────────────┤
│  John: สวัสดีครับ                            │
│  Mary: ทำอะไรอยู่                            │
│  ...                                        │
│  ↑ scrollable chat                          │
├─────────────────────────────────────────────┤
│  ⚡ สถานะ: กำลังอ่านแชต...                    │
└─────────────────────────────────────────────┘
```

## Components

### gui.py — ไฟล์หลัก GUI
- `ChatGUI` class: สร้างหน้าต่าง, จัด layout, bind events
- Background thread สำหรับดึงแชต (ใช้ pytchat เหมือนเดิม)
- Queue ส่งข้อความจาก chat thread → GUI thread
- TTS toggle checkbox

### การทำงาน
```
chat thread                    GUI main thread
    │                               │
    ├── pytchat loop                │
    │   └── sanitize → queue.put()  │
    │                        ┌──────┤
    │                        │ poll │
    │                        ▼      │
    │                   queue.get() │
    │                   display     │
    │                   TTS (ถ้าเปิด)│
```

### Key Behaviors
- **ไม่ block GUI**: chat thread ทำงานแยก, ส่งข้อความผ่าน queue
- **Auto-scroll**: ข้อความใหม่เลื่อนลงอัตโนมัติ
- **TTS toggle**: checkbox, ถ้า unchecked ไม่ TTS
- **Start/Stop**: Start → เริ่ม thread, Stop → หยุด thread + clear chat
- **Error handling**: error แสดงใน status bar

## Data Flow
```
URL input → get_video_id() → chat thread
                                  │
                                  ▼
                          pytchat loop
                                  │
                                  ▼
                          sanitize_message()
                                  │
                                  ▼
                    ┌─────────────┴─────────────┐
                    │  queue.put((name, text))    │
                    └─────────────┬─────────────┘
                                  │
                    GUI poll every 100ms
                                  │
                                  ▼
                          display in chat box
                          TTS ถ้าเปิดอยู่ → speak()
```

## Widgets
- `CTkEntry` — URL input
- `CTkButton` — Start/Stop
- `CTkCheckBox` — TTS toggle
- `CTkTextbox` — chat display (read-only)
- `CTkLabel` — status bar

## Edge Cases
- กด Start ซ้ำ → ignore
- กด Stop ตอนไม่มี chat → ignore
- URL ไม่ถูก → show error ใน status
- TTS error → print warning, ไม่กระทบ GUI
- ปิดหน้าต่างตอน chat ยังทำงาน → หยุด thread + cleanup

## Files Changed
| File | Change |
|------|--------|
| `gui.py` | new file |
| `requirements.txt` | add `customtkinter` |

## Testing
- pytest สำหรับ logic (TTSHandler, sanitize_message)
- GUI test ด้วย unittest mock
