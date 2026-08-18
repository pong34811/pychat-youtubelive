# Configuration constants for pychat-youtubelive

# TTS settings
DEFAULT_TTS_VOICE = "th-TH-NiwatNeural"
MIN_TTS_MESSAGE_LEN = 2  # minimum characters before speaking
MAX_TTS_MESSAGE_LEN = 200  # maximum characters to speak

# Emoji handling regex (used in tts_handler and fix_message)
EMOJI_REGEX = r":[a-zA-Z0-9_]+:"  # simple placeholder pattern

# Default volume (0.0 to 1.0)
DEFAULT_VOLUME = 0.5
