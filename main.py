import asyncio
import sys
from core.logger import setup_logger
from telegram.listener import TelegramListener

# Logger kurulumu
logger = setup_logger()

def main():
    logger.info("============================================")
    logger.info("   TELEGRAM TO TWITTER BOT RUNNING   ")
    logger.info("============================================")

    try:
        listener = TelegramListener()
        asyncio.run(listener.start())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unexpected critical error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()