import tweepy
import time
from core.logger import setup_logger
from .media_uploader import MediaUploader
from utils.formatter import TextFormatter

logger = setup_logger()

class TwitterPublisher:
    def __init__(self, config):
        self.client = tweepy.Client(
            bearer_token=config.TW_BEARER_TOKEN,
            consumer_key=config.TW_API_KEY,
            consumer_secret=config.TW_API_SECRET,
            access_token=config.TW_ACCESS_TOKEN,
            access_token_secret=config.TW_ACCESS_SECRET,
            wait_on_rate_limit=True
        )
        auth = tweepy.OAuth1UserHandler(
            config.TW_API_KEY, config.TW_API_SECRET,
            config.TW_ACCESS_TOKEN, config.TW_ACCESS_SECRET
        )
        self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
        self.uploader = MediaUploader(self.api_v1)

    def post_tweet(self, text, media_paths=None):
        media_ids = []
        if media_paths:
            media_ids = self.uploader.upload_media(media_paths)

        threads = TextFormatter.split_into_threads(text)

        if not threads and media_ids: threads = [""]
        if not threads and not media_ids: return False

        try:
            prev_id = None
            for idx, part in enumerate(threads):
                media = media_ids if idx == 0 else None 
                
                if prev_id:
                    resp = self.client.create_tweet(text=part, in_reply_to_tweet_id=prev_id)
                else:
                    if media:
                        resp = self.client.create_tweet(text=part, media_ids=media)
                    else:
                        resp = self.client.create_tweet(text=part)
                
                prev_id = resp.data['id']
                time.sleep(2)
            
            logger.info(f"Tweet ID: {prev_id}")
            return True
        except Exception as e:
            logger.error(f"Twitter API Error: {e}")
            return False