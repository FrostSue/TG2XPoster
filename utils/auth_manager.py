import json
import os
from core.env_loader import Config
from core.logger import setup_logger

logger = setup_logger()

class AuthManager:
    def __init__(self):
        self.file_path = 'data/sudoers.json'
        self.owner_id = Config.ADMIN_ID  
        self.sudoers = self._load_sudoers()

        if not os.path.exists(self.file_path):
            self._save_sudoers()

    def _load_sudoers(self):
        """Loads the backed-up sudo list."""
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
        except Exception as e:
            logger.error(f"Failed to load sudoers: {e}")
            return []

    def _save_sudoers(self):
        """Saves the list to the file."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.sudoers, f)
        except Exception as e:
            logger.error(f"Failed to save sudoers: {e}")

    def is_owner(self, user_id):
        """Is the user the owner?"""
        return user_id == self.owner_id

    def is_authorized(self, user_id):
        """Is the user either the owner or in the sudo list?"""
        return user_id == self.owner_id or user_id in self.sudoers

    def add_sudo(self, user_id):
        """Add a new sudo (Only the Owner should use this)"""
        if user_id not in self.sudoers and user_id != self.owner_id:
            self.sudoers.append(user_id)
            self._save_sudoers()
            return True
        return False

    def remove_sudo(self, user_id):
        """Remove sudo"""
        if user_id in self.sudoers:
            self.sudoers.remove(user_id)
            self._save_sudoers()
            return True
        return False

    def get_sudo_list(self):
        return self.sudoers
