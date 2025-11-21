import asyncio
import os
from telethon import TelegramClient, events
from core.logger import setup_logger
from core.env_loader import Config
from utils.id_storage import IDStorage
from twitter.publisher import TwitterPublisher

logger = setup_logger()

class TelegramListener:
    def __init__(self):
        self.client = TelegramClient('bot_session', Config.TG_API_ID, Config.TG_API_HASH)
        self.twitter = TwitterPublisher(Config)
        self.storage = IDStorage(Config.DATA_FILE)
        self.album_queue = {} 

    async def start(self):
        Config.ensure_dirs()
        await self.client.start(bot_token=Config.TG_BOT_TOKEN)
        
        self.client.add_event_handler(
            self.handle_message,
            events.NewMessage(chats=Config.TG_CHANNEL_ID)
        )
        logger.info(f"System active. Channel: {Config.TG_CHANNEL_ID}")
        await self.client.run_until_disconnected()

    async def handle_message(self, event):
        msg = event.message
        if self.storage.is_posted(msg.id): return

        if msg.grouped_id:
            await self.process_album(msg)
        else:
            await self.process_single(msg)

    async def process_album(self, message):
        gid = message.grouped_id
        if gid in self.album_queue: return

        self.album_queue[gid] = []
        await asyncio.sleep(3) 
        
        media_files = []
        text = ""
        ids = []
        async for m in self.client.iter_messages(Config.TG_CHANNEL_ID, limit=10):
            if m.grouped_id == gid:
                if self.storage.is_posted(m.id): continue
                ids.append(m.id)
                if m.text and not text: text = m.text
                path = await self.download(m)
                if path: media_files.append(path)

        media_files.reverse()
        
        if media_files:
            logger.info(f"Album: {len(media_files)} file")
            if self.twitter.post_tweet(text, media_files):
                for i in ids: self.storage.add_id(i)
            self.cleanup(media_files)
        
        if gid in self.album_queue: del self.album_queue[gid]

    async def process_single(self, message):
        path = await self.download(message)
        media = [path] if path else []
        
        if self.twitter.post_tweet(message.text, media):
            self.storage.add_id(message.id)
            self.cleanup(media)

    async def download(self, message):
        if message.media:
            try:
                return await self.client.download_media(message, file=Config.TEMP_DIR)
            except:
                return None
        return None

    def cleanup(self, files):
        for f in files:
            if f and os.path.exists(f): os.remove(f)