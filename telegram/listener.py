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
            
            await self.handle_album_chunk(msg)
        else:
            
            await self.process_single(msg)

    async def handle_album_chunk(self, message):
        """
        Collects album parts as they arrive without querying history.
        """
        gid = message.grouped_id
        
        
        if gid in self.album_queue:
            self.album_queue[gid].append(message)
            return

        
        self.album_queue[gid] = [message]
        
        
        asyncio.create_task(self.process_album_worker(gid))

    async def process_album_worker(self, grouped_id):
        """
        Waits for all parts to arrive, then processes them.
        """
        
        await asyncio.sleep(4)

        
        messages = self.album_queue.pop(grouped_id, [])
        if not messages: return

        
        messages.sort(key=lambda x: x.id)

        
        messages = [m for m in messages if not self.storage.is_posted(m.id)]
        if not messages: return

        logger.info(f"Processing album with {len(messages)} items.")

        media_files = []
        text_content = ""
        message_ids = []

        
        for m in messages:
            message_ids.append(m.id)
            if m.text and not text_content: 
                text_content = m.text
            
            path = await self.download_media(m)
            if path: media_files.append(path)

        if media_files:
            success = self.twitter.post_tweet(text_content, media_files)
            if success:
                for mid in message_ids: self.storage.add_id(mid)
                send_log(f"📸 Album Posted!\nFiles: {len(media_files)}\nMessage: {text_content[:50]}...", "SUCCESS")
            else:
                send_log("Album posting failed!", "ERROR")

            self.cleanup_files(media_files)

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