import asyncio
import os
import time
from telethon import TelegramClient, events, Button
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
        self.pending_posts = {} 
        self.pending_edits = {}
        self.recent_posts = {}
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

        self.client.add_event_handler(
            self.handle_callback,
            events.CallbackQuery()
        )

        logger.info(f"System active. Monitoring: {Config.TG_CHANNEL_ID}")
        await self.client.run_until_disconnected()

    async def route_command(self, event):
        await handle_command(event, self)

    async def handle_callback(self, event):
        data = event.data.decode('utf-8')
        user_id = event.sender_id
        
        parts = data.split('_')
        action = parts[0]
        category = parts[1] 
        type_ = parts[2] 
        try:
            msg_id = int(parts[3])
        except IndexError:
            msg_id = 0

        if action == "cancel":
            await event.edit("❌ **Operation Cancelled.**")
            if category == "post":
                if msg_id in self.pending_posts: del self.pending_posts[msg_id]
            elif category == "edit":
                if msg_id in self.pending_edits: del self.pending_edits[msg_id]
            return

        if action == "approve":
            await event.edit("⏳ **Processing...**")
            
            if category == "post":
                if type_ == "single":
                    message = await self.client.get_messages(Config.TG_CHANNEL_ID, ids=msg_id)
                    if message:
                        await self.execute_single_post(message, event)
                    else:
                        await event.edit("⚠️ Message not found.")

                elif type_ == "album":
                    if msg_id not in self.pending_posts:
                        await event.edit("⚠️ Album data timed out.")
                        return
                    album_ids = self.pending_posts.pop(msg_id)
                    messages = await self.client.get_messages(Config.TG_CHANNEL_ID, ids=album_ids)
                    messages = [m for m in messages if m]
                    if messages:
                        await self.execute_album_post(messages, event)
                    else:
                        await event.edit("⚠️ Album messages not found.")

            elif category == "edit":
                if msg_id not in self.pending_edits:
                    await event.edit("⚠️ Edit data timed out.")
                    return
                
                edit_data = self.pending_edits.pop(msg_id)
                old_tweet_id = edit_data['old_tweet_id']

                if type_ == "single":
                    message = await self.client.get_messages(Config.TG_CHANNEL_ID, ids=msg_id)
                    if message:
                        await self.execute_single_post(message, event, old_tweet_id=old_tweet_id)
                    else:
                        await event.edit("⚠️ Message not found.")

                elif type_ == "album":
                    album_ids = edit_data['ids']
                    messages = await self.client.get_messages(Config.TG_CHANNEL_ID, ids=album_ids)
                    messages = [m for m in messages if m]
                    if messages:
                        await self.execute_album_post(messages, event, old_tweet_id=old_tweet_id)
                    else:
                        await event.edit("⚠️ Album messages not found.")

    async def handle_new_message(self, event):
        msg = event.message
        if self.storage.is_posted(msg.id): return

        if msg.grouped_id:
            await self.handle_album_chunk(msg)
        else:
            await self.process_single_request(msg, is_edit=False)

    async def handle_deletion(self, event):
        for msg_id in event.deleted_ids:
            tweet_id = self.storage.get_tweet_id(msg_id)
            if tweet_id:
                if self.twitter.delete_tweet(tweet_id):
                    self.storage.delete_id(msg_id)
                    send_log(f"🗑 **DELETED**\n\nTelegram: `{msg_id}`\nTwitter: `{tweet_id}` removed.", "SUCCESS")

    async def handle_message_edit(self, event):
        msg = event.message
        if not msg: return

        if msg.id in self.recent_posts:
            if time.time() - self.recent_posts[msg.id] < 10:
                return

        await asyncio.sleep(2)

        old_tweet_id = self.storage.get_tweet_id(msg.id)
        if not old_tweet_id:
            return

        if msg.grouped_id:
            msgs = await self.client.get_messages(Config.TG_CHANNEL_ID, min_id=msg.id-9, max_id=msg.id+9)
            album_msgs = [m for m in msgs if m and m.grouped_id == msg.grouped_id]
            album_msgs.sort(key=lambda x: x.id)
            
            if not album_msgs: return
            
            first_msg = album_msgs[0]
            msg_ids = [m.id for m in album_msgs]
            
            self.pending_edits[first_msg.id] = {
                'old_tweet_id': old_tweet_id,
                'ids': msg_ids
            }

            text_preview = first_msg.raw_text[:100] + "..." if first_msg.raw_text else "Album Update"
            buttons = [
                [Button.inline("✅ Apply Change", data=f"approve_edit_album_{first_msg.id}"), 
                 Button.inline("❌ Reject", data=f"cancel_edit_album_{first_msg.id}")]
            ]
            await self.client.send_message(
                Config.LOG_CHANNEL_ID,
                f"📝 **EDIT APPROVAL (ALBUM)**\n\nFiles: {len(album_msgs)}\nText: {text_preview}\n\nDo you want to sync this change?",
                buttons=buttons
            )

        else:
            self.pending_edits[msg.id] = {'old_tweet_id': old_tweet_id}
            text_preview = msg.raw_text[:100] + "..." if msg.raw_text else "Update"
            buttons = [
                [Button.inline("✅ Apply Change", data=f"approve_edit_single_{msg.id}"), 
                 Button.inline("❌ Reject", data=f"cancel_edit_single_{msg.id}")]
            ]
            await self.client.send_message(
                Config.LOG_CHANNEL_ID,
                f"📝 **EDIT APPROVAL**\n\nID: `{msg.id}`\nText: {text_preview}\n\nDo you want to sync this change?",
                buttons=buttons
            )

    async def handle_album_chunk(self, message):
        gid = message.grouped_id
        if gid in self.album_queue:
            self.album_queue[gid].append(message)
            return

        self.album_queue[gid] = [message]
        asyncio.create_task(self.process_album_request(gid))

    async def process_album_request(self, grouped_id):
        await asyncio.sleep(5)
        messages = self.album_queue.pop(grouped_id, [])
        if not messages: return
        messages.sort(key=lambda x: x.id)
        
        if self.storage.is_posted(messages[0].id): return

        first_msg = messages[0]
        msg_ids = [m.id for m in messages]
        self.pending_posts[first_msg.id] = msg_ids
        
        text_preview = first_msg.raw_text[:100] + "..." if first_msg.raw_text else "No Text"
        
        buttons = [
            [Button.inline("✅ Share", data=f"approve_post_album_{first_msg.id}"), 
             Button.inline("❌ Cancel", data=f"cancel_post_album_{first_msg.id}")]
        ]
        
        await self.client.send_message(
            Config.LOG_CHANNEL_ID,
            f"📸 **NEW ALBUM APPROVAL**\n\nFile Count: {len(messages)}\nText: {text_preview}\n\nPlease select action:",
            buttons=buttons
        )

    async def execute_album_post(self, messages, log_event, old_tweet_id=None):
        logger.info(f"Processing album with {len(messages)} items.")
        
        if old_tweet_id:
            await log_event.edit("⏳ **Deleting old tweet...**")
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
            post_time = time.time()
            for mid in message_ids: 
                self.storage.add_id(mid, success_id)
                self.recent_posts[mid] = post_time
            
            tweet_link = f"https://x.com/i/status/{success_id}"
            action_text = "EDIT SYNCED" if old_tweet_id else "ALBUM POSTED"
            await log_event.edit(f"✅ **{action_text}**\nLink: [View]({tweet_link})", link_preview=False)
        else:
            await log_event.edit("❌ **ERROR:** Album posting failed.")
        
        self.cleanup_files(media_files)

    async def process_single_request(self, message, is_edit=False):
        text_preview = message.raw_text[:100] + "..." if message.raw_text else "No Text"
        
        buttons = [
            [Button.inline("✅ Share", data=f"approve_post_single_{message.id}"), 
             Button.inline("❌ Cancel", data=f"cancel_post_single_{message.id}")]
        ]
        
        await self.client.send_message(
            Config.LOG_CHANNEL_ID,
            f"📝 **NEW POST APPROVAL**\n\nID: `{message.id}`\nText: {text_preview}\n\nPlease select action:",
            buttons=buttons
        )

    async def execute_single_post(self, message, log_event, old_tweet_id=None):
        if old_tweet_id:
            await log_event.edit("⏳ **Deleting old tweet...**")
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
            self.recent_posts[message.id] = time.time()
            tweet_link = f"https://x.com/i/status/{success_id}"
            action_text = "EDIT SYNCED" if old_tweet_id else "POST SHARED"
            await log_event.edit(f"✅ **{action_text}**\nLink: [View]({tweet_link})", link_preview=False)
        else:
            await log_event.edit(f"❌ **ERROR:** Failed to post. ID: {message.id}")
        
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