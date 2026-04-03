# FileStreamBot (Railway + Pyrogram)

Simple Telegram bot that turns files you send into public stream/download links, hosted on Railway.

## Features

- Send any file / video / photo to the bot, get:
  - Stream URL
  - Direct download URL
- HTTP range support (seek in video players like VLC / browser)
- Everyone can use the bot
- Only 2 admins can run `/clean` to purge stored files
- Single-file bot (`bot.py`) using:
  - Pyrogram (Telegram)
  - aiohttp (web server)
  - aiofiles (file IO)

---

## Requirements

- Python 3.10+ (Railway default is fine)
- Telegram:
  - `API_ID` and `API_HASH` from https://my.telegram.org
  - Bot token from BotFather
  - Telegram numeric user IDs for the 2 admins (`@baselesssumo` and `@notyokuv`)

Python deps (installed via `requirements.txt`):

- `pyrogram`
- `tgcrypto` (optional speedup)
- `aiohttp`
- `aiofiles`

---

## Local test (optional)

```bash
pip install -r requirements.txt

python bot.py
```

Bot will start on your machine and a local web server will listen on `0.0.0.0:8000`.

> Note: Locally the links will only work from your LAN unless you expose the port.

---

## Deploy to Railway

### 1. Create Railway project

1. Push this repo to GitHub.
2. Go to https://railway.com → New Project → Deploy from GitHub.
3. Select this repo.

Railway will create a service for the bot.

### 2. Configure service

1. In the service → **Settings**:
   - Set **Start Command** to:
     ```bash
     python bot.py
     ```
2. In **Variables** (optional if you don’t hardcode):
   - You can move `API_ID`, `API_HASH`, `BOT_TOKEN` into env vars and read them in `bot.py` if you want.

### 3. Public networking

1. Go to **Networking** tab.
2. Enable **Public Networking**.
3. Copy the generated public URL, e.g.:
   ```text
   https://filestream-bot-production.up.railway.app
   ```

### 4. Set `PUBLIC_BASE` in code

In `bot.py`:

```python
"PUBLIC_BASE": "https://filestream-bot-production.up.railway.app",
```

Replace the value with your actual Railway URL (no trailing slash).

Commit this change to GitHub; Railway will redeploy.

---

## Bot usage

1. Start the bot in Telegram with `/start`.
2. Send any media:
   - Document
   - Video
   - Photo
3. Bot replies with:

   - Stream URL: `https://your-app.up.railway.app/s/XXXXXX`
   - Download URL: `https://your-app.up.railway.app/d/XXXXXX`

Anyone with the link can stream/download the file.

---

## Admin commands

Admins list is configured in `CONFIG["ADMINS"]` in `bot.py` as numeric user IDs.

### `/clean`

```text
/clean
```

- Deletes all stored files from disk.
- Clears `files.json`.
- Only works for users whose IDs are in `ADMINS`.

---

## Notes

- This project uses a very simple JSON file (`files.json`) for storage.
- If you redeploy or the container restarts, previously uploaded files may be lost depending on Railway’s filesystem persistence.
- For heavy/production use, you should:
  - Offload files to S3-like storage,
  - Or use a more robust database and storage layer.
