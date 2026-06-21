import pytest
from tts_handler import TTSHandler


def test_speak_queues_message():
    handler = TTSHandler(voice="th-TH-PremwadeeNeural")
    handler.start()
    handler.speak("John", "สวัสดี")
    assert handler.queue.qsize() == 1
    name, text = handler.queue.get_nowait()
    assert name == "John"
    assert text == "สวัสดี"
    handler.stop()


def test_empty_message_skipped():
    handler = TTSHandler()
    handler.start()
    handler.speak("John", "")
    assert handler.queue.qsize() == 0
    handler.stop()


def test_short_message_skipped():
    handler = TTSHandler()
    handler.start()
    handler.speak("John", "อ")
    assert handler.queue.qsize() == 0
    handler.stop()


def test_emoji_only_message_skipped():
    handler = TTSHandler()
    handler.start()
    handler.speak("John", "\U0001F602\U0001F602")
    assert handler.queue.qsize() == 0
    handler.stop()


def test_long_message_truncated():
    handler = TTSHandler()
    handler.start()
    long_msg = "a" * 300
    handler.speak("John", long_msg)
    name, text = handler.queue.get_nowait()
    assert len(text) <= 200
    handler.stop()


def test_stop_clears_queue():
    handler = TTSHandler()
    handler.start()
    handler.speak("John", "hello")
    handler.stop()
    assert handler.queue.qsize() == 0
