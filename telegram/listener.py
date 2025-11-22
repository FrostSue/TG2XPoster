import asyncio
import os
from telethon import TelegramClient, events
from core.logger import setup_logger
from core.env_loader import Config
from utils.id_storage import IDStorage
from twitter.publisher import TwitterPublisher
from utils.notifier import send_log

logger = setup_logger()

class TelegramListener:
    def __init__(self):
        self.client = TelegramClient('bot_session', Config.TG_API_ID, Config.TG_API_HASH)
        self.twitter = TwitterPublisher(Config)
        self.storage = IDStorage(Config.DATA_FILE)
        self.album_queue = {} 

    async def start(self):
        logger.info("Starting Telegram Listener...")
        Config.ensure_dirs()
        
        await self.client.start(bot_token=Config.TG_BOT_TOKEN)
        
        
        send_log("System started successfully and is monitoring the channel.", "START")
        
        self.client.add_event_handler(
            self.handle_new_message,
            events.NewMessage(chats=Config.TG_CHANNEL_ID)
        )
        
        logger.info(f"System active. Monitoring: {Config.TG_CHANNEL_ID}")
        await self.client.run_until_disconnected()

    async def handle_new_message(self, event):
        msg = event.message
        if self.storage.is_posted(msg.id): return

        if msg.grouped_id:
            await self.process_album(msg)
        else:
            await self.process_single(msg)

    async def process_album(self, message):
        grouped_id = message.grouped_id
        if grouped_id in self.album_queue: return

        self.album_queue[grouped_id] = []
        await asyncio.sleep(3)
        
        media_files = []
        text_content = ""
        message_ids = []

        async for m in self.client.iter_messages(Config.TG_CHANNEL_ID, limit=10):
            if m.grouped_id == grouped_id:
                if self.storage.is_posted(m.id): continue
                message_ids.append(m.id)
                if m.text and not text_content: text_content = m.text
                path = await self.download_media(m)
                if path: media_files.append(path)

        media_files.reverse()
        
        if media_files:
            logger.info(f"Album detected: {len(media_files)} files.")
            success = self.twitter.post_tweet(text_content, media_files)
            if success:
                for mid in message_ids: self.storage.add_id(mid)
                send_log(f"📸 Album Posted!\nFiles: {len(media_files)}\nMessage: {text_content[:50]}...", "SUCCESS")
            else:
                send_log("Album posting failed!", "ERROR")

            self.cleanup_files(media_files)
        
        if grouped_id in self.album_queue: del self.album_queue[grouped_id]

    async def process_single(self, message):
        logger.info(f"New single message: {message.id}")
        media_path = await self.download_media(message)
        media_list = [media_path] if media_path else []
        
        success = self.twitter.post_tweet(message.text, media_list)
        if success:
            self.storage.add_id(message.id)
            msg_preview = message.text[:50] + "..." if message.text else "Media Only"
            send_log(f"Single Content Posted!\nContent: {msg_preview}", "SUCCESS")
        else:
            send_log(f"Single content posting failed! ID: {message.id}", "ERROR")

        self.cleanup_files(media_list)

    async def download_media(self, message):
        if message.media:
            try:
                return await self.client.download_media(message, file=Config.TEMP_DIR)
            except Exception as e:
                logger.error(f"Download error: {e}")
                send_log(f"File download failed: {e}", "ERROR")
                return None
        return None

    def cleanup_files(self, file_paths):
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass