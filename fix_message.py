import re


EMOJI_ALIAS_PATTERN = re.compile(r":[a-z0-9_-]+:")


def sanitize_message(message: str) -> str:
    text = EMOJI_ALIAS_PATTERN.sub("", message.strip()).strip()
    if not text:
        return ""
    return text
