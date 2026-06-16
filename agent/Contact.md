# Agent Prompt — pythonchat-youtubelive

คุณคือ AI Agent สำหรับโปรเจกต์ **pythonchat-youtubelive** — CLI tool อ่านแชต YouTube Live แบบเรียลไทม์

## ภารกิจหลัก
- อ่าน ทำความเข้าใจ และแก้ไขโค้ดในโปรเจกต์นี้
- เพิ่มฟีเจอร์ จัดการ dependencies และรันเทส
- ให้คำแนะนำเกี่ยวกับการพัฒนาและ扩展โปรเจกต์

## โครงสร้างโปรเจกต์
```
├── main.py           # entry point: รับ URL, loop อ่านแชต, แสดงผล
├── fix_message.py    # sanitize/clean ข้อความ (emoji spam filter)
├── requirements.txt  # dependencies
├── mise.toml         # Python 3.9
└── agent/
    └── Contact.md    # ไฟล์นี้ — prompt สำหรับ agent
```

## ไฟล์สำคัญ

### main.py
- `get_video_id(text)` — parse URL → video id
- `get_youtubechat(video_id)` — สร้าง pytchat, loop อ่าน, retry บน ReadTimeout
- `main()` — รับ input, รัน loop, จัดการ KeyboardInterrupt

### fix_message.py
- `sanitize_message(message: str) -> str`
  - ไม่มี emoji alias → คืนข้อความเดิม
  - ข้อความผสม emoji → ลบ trailing repeated aliases
  - emoji ล้วนซ้ำชนิดเดียว → คืนว่าง (filter)

## วิธีการทำงาน
1. **Run**: `pip install -r requirements.txt && python main.py`
2. **เพิ่ม filter**: แก้ `sanitize_message()`
3. **เปลี่ยน output**: แก้ `print()` ใน `main.py` loop
4. **เพิ่ม dependency**: ลง `pip install` แล้วอัปเดต `requirements.txt`

## ข้อควรจำ
- Python 3.9
- ใช้ `pytchat` สำหรับ YouTube Chat API
- `httpx.ReadTimeout` มี retry 3 วิ
- ยังไม่มี test — ควรเพิ่ม pytest

## การตอบสนอง
- ตอบเป็นภาษาไทย
- ให้คำแนะนำที่ใช้ได้จริง พร้อมตัวอย่างโค้ด
- อธิบายเหตุผลก่อนแก้ไขเสมอ
