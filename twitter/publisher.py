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

    def post_tweet(self, text, media_paths=None, quote_id=None):
        media_ids = []
        if media_paths:
            media_ids = self.uploader.upload_media(media_paths)

        threads = TextFormatter.split_into_threads(text)
        if not threads and media_ids: threads = [""]
        if not threads and not media_ids: return None

        try:
            first_tweet_id = None
            previous_tweet_id = None
            for idx, part in enumerate(threads):
                current_media = media_ids if idx == 0 else None
                current_quote_id = quote_id if idx == 0 else None

                if previous_tweet_id:
                    response = self.client.create_tweet(
                        text=part,
                        in_reply_to_tweet_id=previous_tweet_id
                    )
                else:
                    if current_media:
                        response = self.client.create_tweet(
                            text=part,
                            media_ids=current_media,
                            quote_tweet_id=current_quote_id
                        )
                    else:
                        response = self.client.create_tweet(
                            text=part,
                            quote_tweet_id=current_quote_id
                        )
                previous_tweet_id = response.data['id']
                if first_tweet_id is None:
                    first_tweet_id = previous_tweet_id
                time.sleep(2)
            logger.info(f"Tweet posted! ID: {first_tweet_id}")
            return first_tweet_id
        except Exception as e:
            logger.error(f"Twitter API Error: {e}")
            return None

    def delete_tweet(self, tweet_id):
        """
        Deletes a tweet by ID using API v2.
        """
        try:
            self.client.delete_tweet(tweet_id)
            logger.info(f"Tweet deleted successfully: {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete tweet {tweet_id}: {e}")
            return False