import re


EMOJI_ALIAS_PATTERN = re.compile(r":[a-z0-9-]+:")
TRAILING_REPEATED_ALIAS_PATTERN = re.compile(r"(?:\s*(:[a-z0-9-]+:))\1+$")


def sanitize_message(message: str) -> str:
    text = message.strip()
    if not text:
        return ""

    aliases = EMOJI_ALIAS_PATTERN.findall(text)
    if not aliases:
        return text

    joined_aliases = "".join(aliases)
    if joined_aliases != text:
        cleaned_text = TRAILING_REPEATED_ALIAS_PATTERN.sub("", text).rstrip()
        return cleaned_text

    unique_aliases = set(aliases)
    if len(unique_aliases) == 1 and len(aliases) >= 2:
        return ""

    return text
