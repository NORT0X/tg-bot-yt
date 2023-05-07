import os
import re
import yt_dlp
from urllib.parse import urlparse
from telegram import Update, Bot
from telegram.ext import filters, CommandHandler, MessageHandler, ContextTypes, ApplicationBuilder


TOKEN = os.environ.get("BOT_TOKEN")

# Regex for valid url
regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Send me video URL"
    )


async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for processing youtube video links."""
    message = update.message
    if message.text is None:
        message.reply_text("Please provide a valid URL.")
        return

    url = message.text.strip()
    if not is_valid_url(url):
        message.reply_text("Invalid URL format. Please try again.")
        return

    # Download the video
    await message.reply_text("Downloading video...")
    video_path = await download_video(url)
    if not video_path:
        message.reply_text("Failed to download the video.")

    # Send the video back to the user
    converted_video_path = await convert_to_mp4(video_path)
    if not converted_video_path:
        await message.reply_text("Failed to convert video to MP4.")

    with open(converted_video_path, 'rb') as video:
        await context.bot.send_video(update.effective_chat.id, video)
    os.remove(converted_video_path)


async def download_video(url):
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
        except yt_dlp.DownloadError:
            return None


async def convert_to_mp4(video_path):
    converted_path = f"{os.path.splitext(video_path)[0]}.mp4"
    try:
        os.rename(video_path, converted_path)
        return converted_path
    except OSError:
        return None
    

def is_valid_url(url):
    return re.match(regex, url) is not None


def main():
    # Creating downloads folder
    print(TOKEN)
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # Create the bot
    application = ApplicationBuilder().token(TOKEN).build()
    print("Bot started!")

    # Register handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))

    # Start the bot in polling mode
    application.run_polling()


if __name__ == "__main__":
    main()