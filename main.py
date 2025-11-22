import asyncio
import sys
from core.logger import setup_logger
from telegram.listener import TelegramListener
from utils.notifier import send_log

logger = setup_logger()

def main():
    logger.info("============================================")
    logger.info("   STARTING TELEGRAM TO TWITTER BOT       ")
    logger.info("============================================")

    try:
        listener = TelegramListener()
        asyncio.run(listener.start())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        send_log("Bot stopped manually.", "WARNING")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unexpected critical error: {e}", exc_info=True)
        send_log(f"BOT CRASHED! Critical Error:\n{str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()