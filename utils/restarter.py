import sys
import time
from .notifier import send_log
from core.logger import setup_logger

logger = setup_logger()

def restart_bot():
    """
    Safely shuts down the bot.
    Docker automatically restarts thanks to the 'restart: always' policy.
    """
    logger.warning("Restart command received. Shutting down...")
    
    try:
        send_log("🔄 System is restarting via admin command...", "WARNING")
        time.sleep(1)
    except:
        pass

    
    sys.exit(1)