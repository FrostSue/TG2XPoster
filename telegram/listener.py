import asyncio
import os
import datetime
import time
from telethon import TelegramClient, events
from telethon.network import connection
from core.logger import setup_logger
from core.env_loader import Config
from utils.id_storage import IDStorage
from twitter.publisher import TwitterPublisher
from utils.notifier import send_log

logger = setup_logger()

class TelegramListener:
    def __init__(self):
        
        
        
        session_path = 'internal_bot_session'
        
        self.client = TelegramClient(
            session_path,
            Config.TG_API_ID,
            Config.TG_API_HASH,
            connection=connection.ConnectionTcpFull
        )
        self.twitter = TwitterPublisher(Config)
        self.storage = IDStorage(Config.DATA_FILE)
        self.album_queue = {}
        
        
        self.start_time = time.time()
        self.total_tweets = 0

    async def start(self):
        logger.info("Starting Telegram Listener...")
        Config.ensure_dirs()
        
        
        await self.client.start(bot_token=Config.TG_BOT_TOKEN)
        
        send_log("System started successfully.", "START")
        
        
        self.client.add_event_handler(
            self.handle_new_message,
            events.NewMessage(chats=Config.TG_CHANNEL_ID)
        )

        
        
        if Config.ADMIN_ID:
            self.client.add_event_handler(
                self.handle_admin_command,
                events.NewMessage(from_users=[Config.ADMIN_ID])
            )
            logger.info(f"Admin commands enabled for ID: {Config.ADMIN_ID}")
        
        logger.info(f"System active. Monitoring: {Config.TG_CHANNEL_ID}")
        await self.client.run_until_disconnected()

    
    async def handle_admin_command(self, event):
        message = event.message.text.lower().strip()

        
        if message == '/ping':
            await event.reply("🏓 **Pong!** I am alive and listening.")

        
        elif message == '/status':
            uptime_seconds = int(time.time() - self.start_time)
            uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
            
            status_msg = (
                f"📊 **BOT STATUS REPORT**\n\n"
                f"✅ **State:** Running\n"
                f"⏱ **Uptime:** `{uptime_str}`\n"
                f"🐦 **Tweets Sent:** `{self.total_tweets}`\n"
                f"📡 **Monitoring:** `{Config.TG_CHANNEL_ID}`"
            )
            await event.reply(status_msg)

        
        elif message == '/logs':
            try:
                log_file = 'logs/app.log'
                if os.path.exists(log_file):
                    
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        last_logs = "".join(lines[-15:])
                    
                    if not last_logs: last_logs = "No logs yet."
                    
                    
                    if len(last_logs) > 4000: last_logs = last_logs[-4000:]
                    
                    await event.reply(f"📋 **RECENT LOGS**\n\n```text\n{last_logs}\n```")
                else:
                    await event.reply("⚠️ Log file not found.")
            except Exception as e:
                await event.reply(f"❌ Error reading logs: {e}")

    
    async def handle_new_message(self, event):
        msg = event.message
        if self.storage.is_posted(msg.id): return

        if msg.grouped_id:
            await self.handle_album_chunk(msg)
        else:
            await self.process_single(msg)

    async def handle_album_chunk(self, message):
        gid = message.grouped_id
        if gid in self.album_queue:
            self.album_queue[gid].append(message)
            return

        self.album_queue[gid] = [message]
        asyncio.create_task(self.process_album_worker(gid))

    async def process_album_worker(self, grouped_id):
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
            if m.text and not text_content: text_content = m.text
            path = await self.download_media(m)
            if path: media_files.append(path)

        if media_files:
            success = self.twitter.post_tweet(text_content, media_files)
            if success:
                self.total_tweets += 1  
                for mid in message_ids: self.storage.add_id(mid)
                send_log(f"Album Posted! Files: {len(media_files)}", "SUCCESS")
            else:
                send_log("Album posting failed!", "ERROR")
            self.cleanup_files(media_files)

    async def process_single(self, message):
        logger.info(f"New single message: {message.id}")
        media_path = await self.download_media(message)
        media_list = [media_path] if media_path else []
        
        success = self.twitter.post_tweet(message.text, media_list)
        if success:
            self.total_tweets += 1  
            self.storage.add_id(message.id)
            send_log("Single Content Posted!", "SUCCESS")
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
                try: os.remove(path)
                except: pass