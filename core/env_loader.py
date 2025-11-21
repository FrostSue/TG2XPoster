import os
from dotenv import load_dotenv
from .exceptions import ConfigurationError
load_dotenv()

class Config:
    try:
        TG_API_ID = int(os.getenv("TELEGRAM_API_ID"))
        TG_API_HASH = os.getenv("TELEGRAM_API_HASH")
        TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        TG_CHANNEL_ID = int(os.getenv("TELEGRAM_CHANNEL_ID"))

        TW_API_KEY = os.getenv("TWITTER_API_KEY")
        TW_API_SECRET = os.getenv("TWITTER_API_SECRET")
        TW_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
        TW_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
        TW_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

    except (TypeError, ValueError):
        raise ConfigurationError("Missing or incorrect .env configuration!")

    TEMP_DIR = "data/temp"
    DATA_FILE = "data/posted_ids.json"

    @staticmethod
    def ensure_dirs():
        if not os.path.exists(Config.TEMP_DIR):
            os.makedirs(Config.TEMP_DIR)
        if not os.path.exists("data"):
            os.makedirs("data")