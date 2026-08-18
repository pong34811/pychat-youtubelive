# pychat‑youtubelive

## Overview

`pychat‑youtubelive` is a lightweight Python CLI tool that reads live chat messages from a YouTube Live stream, sanitises the text, and speaks each message using Microsoft Edge TTS (`edge‑tts`).  It demonstrates how to combine **async web‑socket chat fetching**, **emoji/text cleaning**, and **audio playback** in a simple, production‑ready package.

## Features

- Real‑time retrieval of YouTube Live chat via `pytchat`.
- Emoji placeholder removal (e.g., `:smile:`) and whitespace trimming.
- Text‑to‑speech using `edge‑tts` with configurable voice, volume, and length limits.
- Centralised logging (console + file) with INFO level by default.
- Clean architecture with separate worker, TTS handler, and utility modules.

## Installation

### Prerequisites
- Python 3.10 or newer.
- `ffmpeg` must be available in your PATH (required by `pygame` for audio playback).

### Quick install
```bash
git clone https://github.com/yourname/pychat‑youtubelive.git
cd pychat‑youtubelive
pip install -r requirements.txt
```

### Editable / development install (recommended)
```bash
pip install -e .
```
This uses the `pyproject.toml` configuration included in the repository.

## Usage

```bash
python -m pychat_youtubelive
```
You will see a prompt:
```
> วางลิงก์ YouTube Live หรือ video id
```
Paste either a full YouTube URL (e.g. `https://www.youtube.com/watch?v=BsI7PXzJl8I`) or just the video ID. The program will start streaming chat messages and speaking them.

### Logging
All operations are logged to the console and to `pychat.log` in the project root.  Example output:
```
[INFO] __main__: วางลิงก์ YouTube Live หรือ video id
[INFO] __main__: กำลังอ่านแชต…
[INFO] __main__: JohnDoe: Hello world!
```

## Configuration
Edit `config/constants.py` to change defaults:
- `DEFAULT_TTS_VOICE` – Azure voice name.
- `MIN_TTS_MESSAGE_LEN` / `MAX_TTS_MESSAGE_LEN` – length thresholds.
- `DEFAULT_VOLUME` – playback volume (0.0–1.0).

## Development

### Running the test suite
```bash
pytest
```
The test suite covers URL parsing, message sanitisation, and the TTS handler start/stop logic (with mocks).

### Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome‑thing`).
3. Write code and tests.
4. Ensure all tests pass (`pytest`).
5. Open a Pull Request with a clear description.

All contributions should follow the coding style enforced by `black` and `flake8`.

## License
MIT © 2026 Your Name
