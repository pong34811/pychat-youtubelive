import time

import httpx
import pytchat

from fix_message import sanitize_message

def get_video_id(text):
    if "v=" in text:
        return text.split("v=")[-1].split("&")[0]
    if "youtu.be/" in text:
        return text.split("youtu.be/")[-1]
    return text  # กรณีใส่เป็น video id ตรงๆ

def get_youtubechat(video_id):
    chat = pytchat.create(video_id=video_id)
    while chat.is_alive():
        try:
            items = chat.get().sync_items()
        except httpx.ReadTimeout:
            print("เชื่อมต่อช้า กำลังลองใหม่ใน 3 วินาที...")
            time.sleep(3)
            continue

        for c in items:
            clean_message = sanitize_message(c.message)
            if not clean_message:
                continue
            print(f"{c.author.name}: {clean_message}")


def main():
    print("วางลิงก์ YouTube Live หรือ video id")
    url = input("> ")

    video_id = get_video_id(url)
    print("กำลังอ่านแชต...\n")

    try:
        get_youtubechat(video_id)
    except KeyboardInterrupt:
        print("หยุดแล้ว")
    except Exception as error:
        print(f"เกิดข้อผิดพลาด: {error}")
        print("ตรวจสอบว่าลิงก์เป็นไลฟ์จริง, แชตเปิดอยู่, และอินเทอร์เน็ตเชื่อมต่อปกติ")

if __name__ == "__main__":
    main()
