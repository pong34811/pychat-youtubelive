# Chat History Log

## 16/6/2569 — สร้างโปรเจกต์และ agent files

- ตรวจสอบโครงสร้างโปรเจกต์ `pythonchat-youtubelive` (main.py, fix_message.py, requirements.txt, mise.toml)
- สร้าง Agent Skill ที่ `~/.config/opencode/skills/pythonchat-youtubelive/SKILL.md` — อธิบายโครงสร้าง ฟังก์ชัน การทำงาน และ common tasks
- สร้างโฟลเดอร์ `agent/` ในโปรเจกต์
- สร้าง `agent/Contact.md` — Prompt สำหรับ AI Agent
- สร้าง `agent/Rule.md` — กฎการพัฒนา 10 ข้อ
- Git commit และ push (`47d0175`)

---

## 16/6/2569 (session 2) — เพิ่มกฎ和完善ระบบ agent

- สร้าง `agent/chat-history.md` — ไฟล์บันทึกประวัติแชท
- อ่าน `.md` ทั้งหมด 3 ไฟล์ก่อนเริ่มงาน (Contact.md, Rule.md, chat-history.md)
- เพิ่มกฎข้อ 0 ใน `Rule.md` — "ก่อนเริ่มงานทุกครั้ง ให้อ่าน .md ทั้งหมดในโปรเจกต์"
- อัปเดต `chat-history.md` ตามที่ user แจ้งเตือน
- สร้าง `agent/Workflow.md` — ASCII Diagram workflow ของโปรแกรม
- สรุป: ทุกครั้งที่ทำงานเสร็จ ต้องกลับมาอัปเดต chat-history.md ด้วย

---

## 21/6/2569 — เพิ่มระบบ TTS (edge-tts)

- brainstorm ฟีเจอร์ TTS, เลือกใช้ **edge-tts** เสียง `th-TH-PremwadeeNeural`
- อัปเดต `agent/Workflow.md` — เพิ่ม TTS step ใน diagram
- สร้าง `agent/Design.md` — design doc
- สร้าง `tts_handler.py` — TTSHandler class: background thread + queue, filter emoji/ข้อความสั้น, truncate 200 chars
- แก้ `main.py` — import TTSHandler, เรียก `tts.speak()` หลัง print
- สร้าง `tests/test_tts_handler.py` — 6 tests ครอบคลุม queue, filter, stop
- อัปเดต `requirements.txt` — เพิ่ม edge-tts, pygame, pytest
- แก้บัค voice name: `Premmawadee` → `Premwadee`
- แก้บัค file lock: เพิ่ม `stop()` + `unload()` ก่อนลบ temp mp3
