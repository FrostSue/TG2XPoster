import os
import time
import datetime
from telethon import events
from core.env_loader import Config
from utils.restarter import restart_bot
from utils.auth_manager import AuthManager


auth = AuthManager()

async def handle_command(event, bot_instance):
    """
    Owner & Sudo Logic.
    """
    sender = await event.get_sender()
    if not sender: return

    if not event.message or not event.message.text: return
    
    raw_text = event.message.text.strip()
    command_parts = raw_text.split()
    if not command_parts: return
    
    
    command = command_parts[0].lower().split('@')[0]
    args = command_parts[1:] 
    
    
    user_id = sender.id
    is_owner = auth.is_owner(user_id)
    is_sudo = auth.is_authorized(user_id) 

    
    
    if command == '/start':
        await event.reply(
            "🤖 **TG2XPoster Active**\n"
            "I am running privately. Unauthorized access is restricted."
        )
        return

    if command == '/help':
        if is_sudo:
            msg = (
                "🛠 **ADMIN COMMANDS**\n\n"
                "📊 `/status` - System stats\n"
                "🏓 `/ping` - Health check\n"
                "📋 `/logs` - View logs\n"
                "🔄 `/restart` - Reboot system\n"
            )
            if is_owner:
                msg += (
                    "\n👑 **OWNER COMMANDS**\n"
                    "➕ `/addsudo <ID>` - Add admin\n"
                    "➖ `/rmsudo <ID>` - Remove admin\n"
                    "📜 `/sudolist` - List admins"
                )
            await event.reply(msg)
        else:
            await event.reply("⛔ Access Denied.")
        return

    
    
    if command in ['/status', '/ping', '/logs', '/restart', '/addsudo', '/rmsudo', '/sudolist']:
        if not is_sudo:
            await event.reply("⛔ **Access Denied:** You are not authorized to manage this bot.")
            return

    
    
    if command == '/ping':
        await event.reply("🏓 **Pong!** System is operational.")

    elif command == '/status':
        uptime_seconds = int(time.time() - bot_instance.start_time)
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
        
        status_msg = (
            f"📊 **SYSTEM STATUS**\n\n"
            f"🛡 **User Role:** {'👑 Owner' if is_owner else '👮 Sudo'}\n"
            f"✅ **State:** Online\n"
            f"⏱ **Uptime:** `{uptime_str}`\n"
            f"🐦 **Tweets:** `{bot_instance.total_tweets}`"
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
                await event.reply(f"📋 **LOGS**\n\n```text\n{last_logs}\n```")
            else:
                await event.reply("⚠️ No logs found.")
        except Exception as e:
            await event.reply(f"❌ Error: {e}")

    elif command == '/restart':
        await event.reply("🔄 **Rebooting...**")
        restart_bot()

    
    
    elif command == '/addsudo':
        if not is_owner:
            await event.reply("⛔ Only the **Owner** can add new admins.")
            return
        
        if not args or not args[0].isdigit():
            await event.reply("❌ Usage: `/addsudo 123456789`")
            return
            
        new_id = int(args[0])
        if auth.add_sudo(new_id):
            await event.reply(f"✅ User `{new_id}` added to Sudo list.")
        else:
            await event.reply("⚠️ User is already authorized or invalid.")

    elif command == '/rmsudo':
        if not is_owner:
            await event.reply("⛔ Only the **Owner** can remove admins.")
            return

        if not args or not args[0].isdigit():
            await event.reply("❌ Usage: `/rmsudo 123456789`")
            return

        target_id = int(args[0])
        if auth.remove_sudo(target_id):
            await event.reply(f"🗑 User `{target_id}` removed from Sudo list.")
        else:
            await event.reply("⚠️ User not found in Sudo list.")

    elif command == '/sudolist':
        if not is_owner: return
        sudoers = auth.get_sudo_list()
        if not sudoers:
            await event.reply("📜 **Sudo List:** Empty (Only Owner).")
        else:
            msg = "📜 **Sudo Users:**\n" + "\n".join([f"- `{uid}`" for uid in sudoers])
            await event.reply(msg)