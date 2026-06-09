import os
import asyncio
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import yt_dlp
import imageio_ffmpeg

# Подключаем ffmpeg
ffmpeg_path = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")

BOT_TOKEN = os.environ["BOT_TOKEN"]
SUPPORTED = ["tiktok.com", "instagram.com"]


def _download(url):
    tmpdir = tempfile.mkdtemp()
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": f"{tmpdir}/%(id)s.%(ext)s",
        "ffmpeg_location": ffmpeg_path,
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            mp4 = path.rsplit(".", 1)[0] + ".mp4"
            if os.path.exists(mp4):
                return mp4
            if os.path.exists(path):
                return path
            return None
    except Exception as e:
        print(f"Download error: {e}")
        return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not any(d in text for d in SUPPORTED):
        await update.message.reply_text("Скинь ссылку из TikTok или Instagram")
        return
    msg = await update.message.reply_text("Скачиваю...")
    filepath = await asyncio.to_thread(_download, text)
    if filepath and os.path.exists(filepath):
        await msg.edit_text("Отправляю...")
        try:
            with open(filepath, "rb") as f:
                await update.message.reply_video(video=f, supports_streaming=True)
        except Exception:
            with open(filepath, "rb") as f:
                await update.message.reply_document(document=f)
        finally:
            os.remove(filepath)
            await msg.delete()
    else:
        await msg.edit_text("Не удалось скачать. Попробуй другую ссылку.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
