# Workflow — pythonchat-youtubelive

```
┌──────────────────────────────────────────────────────────┐
│                     main()                               │
│  1. แสดง "วางลิงก์ YouTube Live หรือ video id"             │
│  2. user input URL / id                                  │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│               get_video_id(text)                         │
│  1. มี "v=" → ตัดเอา value หลัง v= (จนถึง &)              │
│  2. มี "youtu.be/" → ตัดเอาหลัง youtu.be/                │
│  3. อื่นๆ → คืน text ตรงๆ (ถือว่าเป็น video id)           │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│              get_youtubechat(video_id)                   │
│  1. chat = pytchat.create(video_id=video_id)             │
│  2. while chat.is_alive():                               │
│       try:                                               │
│         items = chat.get().sync_items()                  │
│       except httpx.ReadTimeout:                          │
│         รอ 3 วิ แล้ว continue                             │
│                                                          │
│       for c in items:                                    │
│         clean = sanitize_message(c.message)              │
│         ถ้า clean ไม่ว่าง:                                │
│           print(f"{name}: {clean}")                       │
│           tts.speak(f"{name} กล่าวว่า {clean}")           │
│                                                          │
│  3. KeyboardInterrupt → print("หยุดแล้ว")                │
│  4. Exception อื่น → print error + คำแนะนำ               │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│              sanitize_message(message)                   │
│                                                          │
│  text = ลบ emoji aliases ทั้งหมด (:xxx:)                │
│         แล้ว strip()                                     │
│                                                          │
│  ถ้า text ว่าง → return ""                                │
│  ถ้า text มีข้อความ → return text                        │
└──────────────────────────────────────────────────────────┘
```

## Flow สรุป

```
User Input → Parse Video ID → pytchat.connect()
                                    │
                           while chat.is_alive()
                                    │
                           ┌────────┴────────┐
                           │  ReadTimeout?   │
                           └────────┬────────┘
                               Yes  │  No
                               รอ 3 วิ │
                               ┌─────┘
                               ▼
                        fetch sync_items()
                               │
                               ▼
                        for each message
                               │
                               ▼
                        sanitize_message()
                               │
                      ┌────────┴────────┐
                      │  ผ่านหรือโดนfilter?│
                      └────────┬────────┘
                        filter │  ผ่าน
                               │
                               ▼
                         print output
                               │
                               ▼
                          TTS speak()
```

## ประเภท output ปัจจุบัน
```
console:  ผู้ส่ง: ข้อความ
TTS:      {ผู้ส่ง} กล่าวว่า {ข้อความ}
เช่น:     console: John: สวัสดีครับ
          TTS:     John กล่าวว่า สวัสดีครับ
```

## จุดที่สามารถต่อยอด
| จุดใน Flow | สิ่งที่ทำเพิ่มได้ |
|------------|-----------------|
| หลัง sanitize_message | บันทึก raw ลงไฟล์ |
| ก่อน print | แปลภาษา, สรุปด้วย AI |
| ตอนรับ input | รองรับ playlist, channel |
| ใน loop | แยกห้อง, statistics |
| TTS | เลือกเสียง, ความเร็ว, ภาษา, กรองเฉพาะ keyword |
