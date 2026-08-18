import re
import logging
logger = logging.getLogger(__name__)


EMOJI_ALIAS_PATTERN = re.compile(r":[a-z0-9_-]+:")


def sanitize_message(message: str) -> str:
    # Strip leading/trailing whitespace first, then remove emoji placeholders.
    # Do NOT strip again after removal so that trailing spaces left by emoji removal are kept.
    cleaned = EMOJI_ALIAS_PATTERN.sub("", message.strip())
    if not cleaned:
        return ""
    return cleaned
