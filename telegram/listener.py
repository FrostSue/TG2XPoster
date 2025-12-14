import asyncio
import os
import time
from telethon import TelegramClient, events
from telethon.network import connection
from core.logger import setup_logger
from core.env_loader import Config
from utils.id_storage import IDStorage
from twitter.publisher import TwitterPublisher
from utils.notifier import send_log
from .commands import handle_command

logger = setup_logger()

class TelegramListener:
    def __init__(self):
        session_path = os.path.join('data', 'auth')
        self.client = TelegramClient(
            session_path,
            Config.TG_API_ID,
            Config.TG_API_HASH,
            connection=connection.ConnectionTcpFull
        )
        self.twitter = TwitterPublisher(Config)
        self.storage = IDStorage(Config.DATA_FILE)
        self.album_queue = {}
        self.edit_tasks = {}
        self.album_groups = {}
        self.recent_posts = {}
        self.start_time = time.time()
        self.total_tweets = 0
        self.is_paused = False 

    async def start(self):
        logger.info("Starting Telegram Listener...")
        Config.ensure_dirs()
        await self.client.start(bot_token=Config.TG_BOT_TOKEN)
        send_log("System started successfully. Mode: ONLINE", "START")
        
        self.client.add_event_handler(
            self.handle_new_message,
            events.NewMessage(chats=Config.TG_CHANNEL_ID)
        )

        self.client.add_event_handler(
            self.handle_message_edit,
            events.MessageEdited(chats=Config.TG_CHANNEL_ID)
        )

        self.client.add_event_handler(
            self.handle_deletion,
            events.MessageDeleted(chats=Config.TG_CHANNEL_ID)
        )

        self.client.add_event_handler(
            self.route_command,
            events.NewMessage(pattern='/')
        )

        logger.info(f"System active. Monitoring: {Config.TG_CHANNEL_ID}")
        await self.client.run_until_disconnected()

    async def route_command(self, event):
        await handle_command(event, self)

    async def handle_new_message(self, event):
        if self.is_paused:
            return 

        msg = event.message
        if self.storage.is_posted(msg.id): return

        if msg.grouped_id:
            await self.handle_album_chunk(msg)
        else:
            await self.process_single_auto(msg)

    async def handle_deletion(self, event):
        if self.is_paused: return 

        for msg_id in event.deleted_ids:
            tweet_id = self.storage.get_tweet_id(msg_id)
            if tweet_id:
                if self.twitter.delete_tweet(tweet_id):
                    self.storage.delete_id(msg_id)
                    send_log(f"🗑 **DELETED**\n\nTelegram: `{msg_id}`\nTwitter: `{tweet_id}` removed.", "SUCCESS")

    async def handle_message_edit(self, event):
        if self.is_paused: return

        msg = event.message
        if not msg: return

        if msg.id in self.edit_tasks:
            self.edit_tasks[msg.id].cancel()
        
        task = asyncio.create_task(self.process_edit_worker(msg.id, msg.grouped_id))
        self.edit_tasks[msg.id] = task

    async def process_edit_worker(self, msg_id, grouped_id):
        try:
            await asyncio.sleep(5)
            
            msg = await self.client.get_messages(Config.TG_CHANNEL_ID, ids=msg_id)
            if not msg: return

            old_tweet_id = self.storage.get_tweet_id(msg.id)
            if not old_tweet_id:
                return

            logger.info(f"Auto-Syncing edit for Msg {msg.id}")

            if grouped_id:
                album_msgs = []
                if msg.id in self.album_groups:
                    group_ids = self.album_groups[msg.id]
                    album_msgs = await self.client.get_messages(Config.TG_CHANNEL_ID, ids=group_ids)
                    album_msgs = [m for m in album_msgs if m]
                else:
                    potential_ids = list(range(msg.id - 9, msg.id + 10))
                    msgs = await self.client.get_messages(Config.TG_CHANNEL_ID, ids=potential_ids)
                    album_msgs = [m for m in msgs if m and m.grouped_id == grouped_id]

                album_msgs.sort(key=lambda x: x.id)
                if not album_msgs: return
                
                await self.execute_album_post(album_msgs, old_tweet_id=old_tweet_id)
            else:
                await self.execute_single_post(msg, old_tweet_id=old_tweet_id)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in edit worker: {e}")
        finally:
            if msg_id in self.edit_tasks:
                del self.edit_tasks[msg_id]

    async def handle_album_chunk(self, message):
        gid = message.grouped_id
        if gid in self.album_queue:
            self.album_queue[gid].append(message)
            return

        self.album_queue[gid] = [message]
        asyncio.create_task(self.process_album_auto(gid))

    async def process_album_auto(self, grouped_id):
        await asyncio.sleep(5)
        messages = self.album_queue.pop(grouped_id, [])
        if not messages: return
        messages.sort(key=lambda x: x.id)
        
        if self.storage.is_posted(messages[0].id): return
        
        msg_ids = [m.id for m in messages]
        for mid in msg_ids:
            self.album_groups[mid] = msg_ids

        await self.execute_album_post(messages)

    async def execute_album_post(self, messages, old_tweet_id=None):
        logger.info(f"Posting album with {len(messages)} items.")
        
        if old_tweet_id:
            self.twitter.delete_tweet(old_tweet_id)

        media_files = []
        text_content = ""
        message_ids = []
        quote_id = None
        first_msg = messages[0]
        
        if first_msg.is_reply:
            reply = await first_msg.get_reply_message()
            if reply:
                quote_id = self.storage.get_tweet_id(reply.id)

        for m in messages:
            message_ids.append(m.id)
            if m.raw_text and not text_content: 
                text_content = m.raw_text
            path = await self.download_media(m)
            if path: media_files.append(path)

        success_id = self.twitter.post_tweet(text_content, media_files, quote_id=quote_id)
        
        if success_id:
            self.total_tweets += 1
            for mid in message_ids: 
                self.storage.add_id(mid, success_id)
                self.album_groups[mid] = [x.id for x in messages]
            
            tweet_link = f"https://x.com/i/status/{success_id}"
            action = "EDIT SYNCED" if old_tweet_id else "ALBUM POSTED"
            send_log(f"✅ **{action}**\nLink: [View]({tweet_link})", "SUCCESS")
        else:
            send_log("❌ **ERROR:** Album posting failed.", "ERROR")
        
        self.cleanup_files(media_files)

    async def process_single_auto(self, message):
        await self.execute_single_post(message)

    async def execute_single_post(self, message, old_tweet_id=None):
        if old_tweet_id:
            self.twitter.delete_tweet(old_tweet_id)

        media_path = await self.download_media(message)
        media_list = [media_path] if media_path else []
        quote_id = None
        if message.is_reply:
            reply = await message.get_reply_message()
            if reply:
                quote_id = self.storage.get_tweet_id(reply.id)

        text_content = message.raw_text

        success_id = self.twitter.post_tweet(text_content, media_list, quote_id=quote_id)
        
        if success_id:
            self.total_tweets += 1
            self.storage.add_id(message.id, success_id)
            tweet_link = f"https://x.com/i/status/{success_id}"
            action = "EDIT SYNCED" if old_tweet_id else "POST SHARED"
            send_log(f"✅ **{action}**\nLink: [View]({tweet_link})", "SUCCESS")
        else:
            send_log(f"❌ **ERROR:** Failed to post ID {message.id}", "ERROR")
        
        self.cleanup_files(media_list)

    async def download_media(self, message):
        if message.media:
            try:
                return await self.client.download_media(message, file=Config.TEMP_DIR)
            except Exception as e:
                logger.error(f"Download error: {e}")
                return None
        return None

    def cleanup_files(self, file_paths):
        for path in file_paths:
            if path and os.path.exists(path):
                try: os.remove(path)
                except: pass