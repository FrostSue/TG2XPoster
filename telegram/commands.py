import os
import time
import datetime
from telethon import events, functions, types
from core.env_loader import Config
from utils.restarter import restart_bot

async def is_user_admin(client, chat_id, user_id):
    """
    Checks if the user is an administrator in the CURRENT chat (Group).
    """ 
    if chat_id == user_id:
        return False

    try:
        participant = await client(functions.channels.GetParticipantRequest(
            channel=chat_id,
            participant=user_id
        ))
        
        if isinstance(participant.participant, (types.ChannelParticipantAdmin, types.ChannelParticipantCreator)):
            return True
        return False
    except Exception:
        return False

async def handle_command(event, bot_instance):
    """
    Central command handler.
    """
    sender = await event.get_sender()
    if not sender: return
    if not event.message or not event.message.text: return
    command_parts = event.message.text.lower().strip().split()
    if not command_parts: return
    command = command_parts[0]
    chat_id = event.chat_id
    
    
    if command == '/start':
        intro_msg = (
            "🤖 **Hello! I am TG2XPoster.**\n\n"
            "I automatically mirror content from Telegram to X (Twitter).\n"
            "Add me to a management group to control me.\n\n"
            "ℹ️ Type `/help` to see available commands."
        )
        await event.reply(intro_msg)
        return

    if command == '/help':
        help_msg = (
            "🛠 **AVAILABLE COMMANDS**\n"
            "*(Only for Group Admins)*\n\n"
            "🟢 `/status` - View uptime and tweet stats\n"
            "🏓 `/ping` - Check if bot is alive\n"
            "📋 `/logs` - View recent system logs\n"
            "🔄 `/restart` - Restart the bot process\n\n"
            "⚠️ *Note: Commands must be sent in a group where you are an admin.*"
        )
        await event.reply(help_msg)
        return

    
    is_admin = await is_user_admin(bot_instance.client, chat_id, sender.id)

    if not is_admin:
        if chat_id == sender.id:
            await event.reply("⛔ **Access Denied:** Admin commands usually work in groups, not in DM.")
        else:
            await event.reply("⛔ **Access Denied:** You must be an administrator of this group.")
        return

    
    if command == '/ping':
        await event.reply("🏓 **Pong!** System is active.")

    elif command == '/status':
        uptime_seconds = int(time.time() - bot_instance.start_time)
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
        
        status_msg = (
            f"📊 **SYSTEM STATUS**\n\n"
            f"✅ **State:** Online\n"
            f"⏱ **Uptime:** `{uptime_str}`\n"
            f"🐦 **Total Tweets:** `{bot_instance.total_tweets}`\n"
            f"📡 **Monitored Channel:** `{Config.TG_CHANNEL_ID}`"
        )
        await event.reply(status_msg)

    elif command == '/logs':
        try:
            log_file = 'logs/app.log'
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    last_logs = "".join(lines[-15:]) 
                
                if len(last_logs) > 4000: last_logs = last_logs[-4000:]
                await event.reply(f"📋 **SYSTEM LOGS**\n\n```text\n{last_logs}\n```")
            else:
                await event.reply("⚠️ Log file is empty or missing.")
        except Exception as e:
            await event.reply(f"❌ Error fetching logs: {e}")

    elif command == '/restart':
        await event.reply("🔄 **Rebooting system...**\nBot will be back in ~10 seconds.")
        restart_bot()