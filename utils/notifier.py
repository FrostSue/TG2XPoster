import requests
from core.env_loader import Config
from core.logger import setup_logger

logger = setup_logger()

def send_log(message, level="INFO"):
    """
    Sends a message to the specified log channel.
    Level: INFO (Green/Normal), ERROR (Red/Error), WARNING (Yellow/Warning)
    """
    if not Config.LOG_CHANNEL_ID:
        return

    emoji = "ℹ️"
    if level == "ERROR": emoji = "🚨"
    elif level == "WARNING": emoji = "⚠️"
    elif level == "SUCCESS": emoji = "✅"
    elif level == "START": emoji = "🚀"

    formatted_msg = f"{emoji} **[{level}]**\n\n{message}"

    url = f"https://api.telegram.org/bot{Config.TG_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": Config.LOG_CHANNEL_ID,
        "text": formatted_msg,
        "parse_mode": "Markdown" 
    }

    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        logger.error(f"Log could not be sent: {e}")