import os
import asyncio
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = os.environ["BOT_TOKEN"]

async def download_video(url: str) -> str | None:
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": "%(id)s.%(ext)s",
        "merge_output_format": "mp4",
        # TikTok без вотермарки
        "extractor_args": {"tiktok": {"webpage_download": True}},
        "quiet": True,
        "no_warnings": True,
    }
    
    tmpdir = tempfile.mkdtemp()
    ydl_opts["outtmpl"] = f"{tmpdir}/%(id)s.%(ext)s"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not filename.endswith(".mp4"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"
            return filename
    except Exception as e:
        print(f"Download error: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Проверяем, что это ссылка
    if not any(domain in text for domain in ["tiktok.com", "instagram.com", "youtube.com/shorts", "youtu.be"]):
        await update.message.reply_text(
            "Скинь ссылку на видео из TikTok, Instagram или YouTube Shorts 👇"
        )
        return
    
    msg = await update.message.reply_text("⏳ Скачиваю...")
    
    filepath = await asyncio.to_thread(download_sync, text)
    
    if filepath and os.path.exists(filepath):
        await msg.edit_text("📤 Отправляю...")
        try:
            with open(filepath, "rb") as video:
                await update.message.reply_video(
                    video=video,
                    supports_streaming=True,
                )
            await msg.delete()
        except Exception:
            # Если файл слишком большой — отправляем как документ
            with open(filepath, "rb") as video:
                await update.message.reply_document(document=video)
            await msg.delete()
        finally:
            os.remove(filepath)
    else:
        await msg.edit_text("❌ Не удалось скачать. Попробуй другую ссылку.")

def download_sync(url: str) -> str | None:
    """Синхронная обёртка для asyncio.to_thread"""
    return asyncio.run(download_video(url)) if False else _download(url)

def _download(url: str) -> str | None:
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "extractor_args": {"tiktok": {"webpage_download": True}},
        "quiet": True,
        "no_warnings": True,
    }
    tmpdir = tempfile.mkdtemp()
    ydl_opts["outtmpl"] = f"{tmpdir}/%(id)s.%(ext)s"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not filename.endswith(".mp4"):
                base = filename.rsplit(".", 1)[0]
                mp4 = base + ".mp4"
                if os.path.exists(mp4):
                    return mp4
            return filename if os.path.exists(filename) else None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
