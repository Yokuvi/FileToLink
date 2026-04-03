# 🔥 AUTO CONFIG - Edit ONLY if you change creds or IP
CONFIG = {
    "API_ID": 30517699,
    "API_HASH": "131560a9f8adae13d709db10b187113d",
    "BOT_TOKEN": "8435515046:AAEufFAljIyIPipZIq8yFPMFInRt6ZsrmhA",

    # Bind address + port for the web server
    "FQDN": "0.0.0.0",
    "PORT": 8080,

    # Public URL that Telegram users will open
    # Use your Wi-Fi IPv4 here:
    "PUBLIC_BASE": "http://10.97.115.200:8080",

    "OWNER_ID": 8233622426,
}

import os
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
from aiohttp import web
import aiofiles
import threading
from datetime import datetime
import json
import hashlib
import base64

# ------------- BASIC CONFIG -------------

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

API_ID = CONFIG["API_ID"]
API_HASH = CONFIG["API_HASH"]
BOT_TOKEN = CONFIG["BOT_TOKEN"]
FQDN = CONFIG["FQDN"]
PORT = CONFIG["PORT"]
OWNER_ID = CONFIG["OWNER_ID"]
PUBLIC_BASE = CONFIG["PUBLIC_BASE"].rstrip("/")

app = Client("FileStreamEasy", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

STORAGE_FILE = "files.json"
if not os.path.exists(STORAGE_FILE):
    with open(STORAGE_FILE, "w") as f:
        json.dump({}, f)


def load_files():
    with open(STORAGE_FILE, "r") as f:
        return json.load(f)


def save_files(files):
    with open(STORAGE_FILE, "w") as f:
        json.dump(files, f)


def short_id(file_id: str) -> str:
    hash_obj = hashlib.md5(file_id.encode())
    return base64.urlsafe_b64encode(hash_obj.digest()[:6]).decode()[:6]


# ------------- WEB SERVER -------------

async def stream_handler(request: web.Request):
    shortid = request.match_info.get("shortid")
    all_files = load_files()

    for file_id, data in all_files.items():
        if short_id(file_id) == shortid:
            file_path = data["path"]
            if not os.path.exists(file_path):
                return web.Response(status=404, text="File expired/deleted")

            range_header = request.headers.get("Range")
            start = 0
            if range_header:
                try:
                    start_str = range_header.split("=")[1].split("-")[0]
                    start = int(start_str)
                except Exception:
                    start = 0

            stat = os.stat(file_path)
            size = stat.st_size

            async with aiofiles.open(file_path, "rb") as f:
                await f.seek(start)
                chunk = await f.read(1024 * 1024)  # 1 MB

                headers = {
                    "Content-Length": str(len(chunk)),
                    "Accept-Ranges": "bytes",
                    "Content-Type": "application/octet-stream",
                    "Content-Disposition": f'attachment; filename="{data["name"]}"',
                }
                if range_header:
                    headers["Content-Range"] = f"bytes {start}-{start + len(chunk) - 1}/{size}"

                return web.Response(
                    body=chunk,
                    headers=headers,
                    status=206 if range_header else 200,
                )

    return web.Response(status=404, text="File not found")


async def web_server():
    aio_app = web.Application()
    aio_app.router.add_get("/s/{shortid}", stream_handler)
    aio_app.router.add_get("/d/{shortid}", stream_handler)
    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, FQDN, PORT)
    await site.start()
    log.info(f"🚀 Public stream server: http://{FQDN}:{PORT}/s/SHORTID")


def start_web():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(web_server())
    loop.run_forever()


web_thread = threading.Thread(target=start_web, daemon=True)
web_thread.start()


# ------------- BOT HANDLERS -------------

@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    await message.reply(
        "**🎉 FileStreamBot Ready!**\n\n"
        "📤 Send any **file/video/photo**\n"
        "🔗 Get **public direct link** instantly!\n\n"
        "**Works everywhere:** Browser, VLC, IDM, mobile\n"
        "**No login needed!** Share with anyone 🌐",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📚 Help", callback_data="help")]]
        ),
    )


@app.on_message(filters.media & filters.private)
async def handle_media(client: Client, message: Message):
    wait_msg = await message.reply("⏳ Processing your file... (10 sec max)")

    file_id = str(message.id)
    sid = short_id(file_id)

    os.makedirs("files", exist_ok=True)
    file_path = f"files/{file_id}"

    try:
        await client.download_media(message, file_path)

        name = "file"
        size = 0
        if message.document:
            name = message.document.file_name or name
            size = message.document.file_size or 0
        elif message.video:
            name = getattr(message.video, "file_name", name) or name
            size = message.video.file_size or 0
        elif message.photo:
            name = "photo.jpg"
            size = 0

        name = name.replace(" ", "_")

        files = load_files()
        files[file_id] = {
            "name": name,
            "path": file_path,
            "size": size,
            "time": str(datetime.now()),
        }
        save_files(files)

        stream_link = f"{PUBLIC_BASE}/s/{sid}"
        download_link = f"{PUBLIC_BASE}/d/{sid}"

        caption = f"""
**✅ File Ready!**

📁 **{files[file_id]['name']}**
📊 **{files[file_id]['size'] / 1024 / 1024:.1f} MB**

🔗 **Stream:** `{stream_link}`
⬇️ **Download:** `{download_link}`

✨ **Public - No login!** Share anywhere!
""".strip()

        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🎥 Stream", url=stream_link)],
                [InlineKeyboardButton("⬇️ Download", url=download_link)],
                [InlineKeyboardButton("➕ More Files", callback_data="more")],
            ]
        )

        await wait_msg.delete()
        await message.reply(caption, reply_markup=kb)

    except Exception as e:
        await wait_msg.delete()
        await message.reply(f"❌ Error: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)


@app.on_callback_query(filters.regex(r"help|more"))
async def cb_handler(client: Client, query):
    if query.data == "help":
        await query.answer(
            "Send file → Get link → Share anywhere!\n"
            "Supports video seeking in browser/VLC 📹",
            show_alert=True,
        )
    else:
        await query.answer("Send more files! 😊", show_alert=True)


@app.on_message(filters.command("clean") & filters.user(OWNER_ID))
async def clean(client: Client, message: Message):
    files = load_files()
    deleted = 0
    for fid in list(files.keys()):
        path = files[fid]["path"]
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted += 1
            except Exception:
                pass
        del files[fid]
    save_files(files)
    await message.reply(f"🧹 Cleaned {deleted} files")


if __name__ == "__main__":
    print("🤖 Starting SUPER EASY FileStreamBot...")
    print(f"🌐 Links like: {PUBLIC_BASE}/s/ABC123")
    app.run()
