import tweepy
import os
from core.logger import setup_logger

logger = setup_logger()

class MediaUploader:
    def __init__(self, api_v1):
        self.api = api_v1

    def upload_media(self, file_paths):
        media_ids = []
        for path in file_paths:
            try:
                if not os.path.exists(path): continue
 
                if path.lower().endswith(('.mp4', '.mov', '.gif')):
                    media = self.api.media_upload(path, chunked=True, media_category='tweet_video')
                else:
                    media = self.api.media_upload(path)
                
                media_ids.append(media.media_id)
            except Exception as e:
                logger.error(f"Media upload error ({path}): {e}")
        return media_ids