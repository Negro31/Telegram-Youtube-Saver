import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv
from utils.downloader import download_video, get_video_info
from utils.helpers import is_valid_youtube_url, cleanup_file

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komutu - Hoş geldin mesajı"""
    welcome_text = (
        "🎥 *YouTube Video İndirme Botu*\n\n"
        "Merhaba! YouTube videolarını istediğiniz formatta indirebilirsiniz.\n\n"
        "📋 *Kullanım:*\n"
        "• YouTube video linkini gönderin\n"
        "• Format ve kalite seçin\n"
        "• Videonuz hazır!\n\n"
        "🎯 *Desteklenen Formatlar:*\n"
        "• MP4 (360p-2160p)\n"
        "• MP3 (128-320kbps)\n"
        "• Sadece Ses (m4a, webm)\n"
        "• Sadece Video\n\n"
        "⚠️ *Not:* Telegram 2GB dosya limiti vardır."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """YouTube URL'si alındığında format seçim menüsü göster"""
    url = update.message.text.strip()
    
    if not is_valid_youtube_url(url):
        await update.message.reply_text(
            "❌ Geçersiz YouTube linki. Lütfen geçerli bir YouTube URL'si gönderin."
        )
        return
    
    status_msg = await update.message.reply_text("🔍 Video bilgileri alınıyor...")
    
    try:
        video_info = await get_video_info(url)
        
        if not video_info:
            await status_msg.edit_text("❌ Video bilgileri alınamadı. Lütfen başka bir link deneyin.")
            return
        
        context.user_data['video_url'] = url
        context.user_data['video_title'] = video_info.get('title', 'Bilinmeyen')
        
        keyboard = [
            [
                InlineKeyboardButton("🎬 MP4 360p", callback_data="mp4_360"),
                InlineKeyboardButton("🎬 MP4 480p", callback_data="mp4_480")
            ],
            [
                InlineKeyboardButton("🎬 MP4 720p", callback_data="mp4_720"),
                InlineKeyboardButton("🎬 MP4 1080p", callback_data="mp4_1080")
            ],
            [
                InlineKeyboardButton("🎬 MP4 1440p", callback_data="mp4_1440"),
                InlineKeyboardButton("🎬 MP4 2160p", callback_data="mp4_2160")
            ],
            [
                InlineKeyboardButton("🎵 MP3 128kbps", callback_data="mp3_128"),
                InlineKeyboardButton("🎵 MP3 192kbps", callback_data="mp3_192"),
                InlineKeyboardButton("🎵 MP3 320kbps", callback_data="mp3_320")
            ],
            [
                InlineKeyboardButton("🔊 Sadece Ses (M4A)", callback_data="audio_m4a"),
                InlineKeyboardButton("🔊 Sadece Ses (WEBM)", callback_data="audio_webm")
            ],
            [
                InlineKeyboardButton("📹 Sadece Video (En İyi)", callback_data="video_only")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        info_text = (
            f"📹 *Video Bulundu*\n\n"
            f"*Başlık:* {video_info.get('title', 'Bilinmeyen')[:100]}\n"
            f"*Süre:* {video_info.get('duration_string', 'Bilinmeyen')}\n\n"
            f"Lütfen indirmek istediğiniz format ve kaliteyi seçin:"
        )
        
        await status_msg.edit_text(info_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Video bilgisi alma hatası: {e}")
        await status_msg.edit_text(
            "❌ Video bilgileri alınırken bir hata oluştu. Lütfen tekrar deneyin."
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buton seçimlerini işle"""
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('video_url')
    if not url:
        await query.edit_message_text("❌ Hata: Video URL'si bulunamadı. Lütfen tekrar link gönderin.")
        return
    
    choice = query.data
    format_type, quality = choice.split('_')
    
    status_msg = await query.edit_message_text("⏳ İndirme başlatılıyor...")
    
    try:
        await status_msg.edit_text("📥 Video indiriliyor... Lütfen bekleyin.")
        
        file_path = await download_video(url, format_type, quality)
        
        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text("❌ İndirme başarısız. Lütfen tekrar deneyin.")
            return
        
        file_size = os.path.getsize(file_path)
        
        if file_size > 2 * 1024 * 1024 * 1024:
            await status_msg.edit_text(
                "❌ Dosya çok büyük (>2GB). Telegram limitini aşıyor. "
                "Lütfen daha düşük kalite seçin."
            )
            cleanup_file(file_path)
            return
        
        await status_msg.edit_text("📤 Dosya gönderiliyor...")
        
        video_title = context.user_data.get('video_title', 'video')
        caption = f"✅ *{video_title[:100]}*\n\n🎯 Format: {format_type.upper()} {quality}"
        
        if format_type in ['mp3', 'audio']:
            with open(file_path, 'rb') as audio_file:
                await query.message.reply_audio(
                    audio=audio_file,
                    caption=caption,
                    parse_mode='Markdown'
                )
        else:
            with open(file_path, 'rb') as video_file:
                await query.message.reply_video(
                    video=video_file,
                    caption=caption,
                    parse_mode='Markdown',
                    supports_streaming=True
                )
        
        await status_msg.delete()
        
        cleanup_file(file_path)
        
    except Exception as e:
        logger.error(f"İndirme hatası: {e}")
        await status_msg.edit_text(
            f"❌ Bir hata oluştu:\n`{str(e)[:200]}`\n\n"
            "Lütfen başka bir format veya kalite deneyin.",
            parse_mode='Markdown'
        )
        if 'file_path' in locals():
            cleanup_file(file_path)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hata yöneticisi"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin."
        )

def main():
    """Bot'u başlat"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN bulunamadı! .env dosyasını kontrol edin.")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.add_error_handler(error_handler)
    
    logger.info("🤖 Bot başlatılıyor...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
