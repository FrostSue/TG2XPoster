import json
import os
from core.logger import setup_logger

logger = setup_logger()

class IDStorage:
    def __init__(self, filepath):
        self.filepath = filepath
        self.posted_ids = self._load_ids()

    def _load_ids(self):
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def is_posted(self, message_id):
        return message_id in self.posted_ids

    def add_id(self, message_id):
        if message_id not in self.posted_ids:
            self.posted_ids.append(message_id)
            self._save_ids()

    def _save_ids(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.posted_ids, f)
        except Exception as e:
            logger.error(f"ID registration error: {e}")