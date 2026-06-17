# Rules — pythonchat-youtubelive

## กฎการพัฒนา

0. **ก่อนเริ่มงานทุกครั้ง ให้อ่าน .md ทั้งหมดในโปรเจกต์** — `agent/Contact.md`, `agent/Rule.md`, `agent/chat-history.md` เพื่อทำความเข้าใจบริบทและประวัติ

1. **ไม่แตกไฟล์หลักโดยไม่จำเป็น** — `main.py` และ `fix_message.py` เป็น core ถ้าจะเพิ่มฟีเจอร์ใหญ่ ให้แยกเป็นไฟล์ใหม่ใน `agent/` หรือ `modules/`

2. **ทุกฟังก์ชันต้องมี type hint** — ใช้ `def func(arg: str) -> bool:` เสมอ

3. **ห้ามแก้ `requirements.txt` ด้วยมือ** — ใช้ `pip freeze > requirements.txt` หรือ `pip install package && pip freeze | Select-String package >> requirements.txt`

4. **Commit message ต้องสื่อความหมาย** — รูปแบบ: `[ประเภท] สิ่งที่ทำ` เช่น `[fix] handle connection timeout gracefully`, `[feat] add JSON output mode`

5. **ก่อน commit ต้อง check**:
   - ไม่มี `print()` debug ทิ้งไว้
   - ไม่มี API key/token hardcode
   - รันแล้วไม่ error

6. **error handling** — `try/except` ทุกจุดที่เรียก network (pytchat, httpx)

7. **input validation** — `get_video_id()` ต้อง handle ทั้ง URL เต็ม, short link, และ plain video id

8. **performance** — อย่า block main loop ด้วยงาน heavy ถ้าจำเป็นให้ใช้ `threading` หรือ `asyncio`

9. **ภาษา** — comment และ variable name เป็นอังกฤษ, user-facing message เป็นไทย

10. **testing** — ถ้าเพิ่ม logic ใหม่ใน `fix_message.py` ต้องเพิ่ม test cases ใน `tests/` (ถ้ามี)

## การ review โค้ด
- logic ซ้ำ → สร้าง helper function
- magic number/string → ใช้ constant หรือ enum
- import เฉพาะที่จำเป็นเท่านั้น
- PEP 8 ยึดหยุ่นได้ แต่ต้อง consistent
