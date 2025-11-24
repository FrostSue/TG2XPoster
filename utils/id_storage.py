import json
import os
from core.logger import setup_logger

logger = setup_logger()

class IDStorage:
    def __init__(self, filepath):
        self.filepath = filepath
        self.posted_data = self._load_data()

    def _load_data(self):
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list): return {}
                return data
        except json.JSONDecodeError:
            return {}

    def get_tweet_id(self, tg_message_id):
        """Retrieves the Twitter ID associated with a Telegram Message ID."""
        return self.posted_data.get(str(tg_message_id))

    def is_posted(self, tg_message_id):
        return str(tg_message_id) in self.posted_data

    def add_id(self, tg_message_id, twitter_tweet_id):
        self.posted_data[str(tg_message_id)] = str(twitter_tweet_id)
        self._save_data()

    def _save_data(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.posted_data, f)
        except Exception as e:
            logger.error(f"Failed to save ID data: {e}")