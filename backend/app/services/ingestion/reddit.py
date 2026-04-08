"""Reddit ingestion via PRAW"""

from datetime import datetime
from typing import List, Dict, Any

from ...config import Config
from ...utils.logger import get_logger

logger = get_logger('foresight.ingestion.reddit')


class RedditService:
    def __init__(self):
        self.client_id = Config.get("reddit_client_id")
        self.client_secret = Config.get("reddit_client_secret")
        self.user_agent = Config.REDDIT_USER_AGENT
        self._reddit = None

    @property
    def source_name(self):
        return "reddit"

    def _get_reddit(self):
        if self._reddit is None:
            import praw
            logger.info(f"[Reddit] Initializing PRAW client (agent={self.user_agent})")
            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
        return self._reddit

    def fetch_mentions(self, keywords, negative_keywords=None, since=None):
        if not self.client_id or not self.client_secret:
            logger.warning("[Reddit] Credentials not configured — set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET via Settings")
            return []

        query = " OR ".join(keywords)
        if negative_keywords:
            for nk in negative_keywords:
                query += f" NOT {nk}"

        logger.info(f"[Reddit] Searching r/all: query='{query}', sort=new, time=day, limit=50")

        try:
            reddit = self._get_reddit()

            mentions = []
            for submission in reddit.subreddit("all").search(query, sort="new", time_filter="day", limit=50):
                published = datetime.utcfromtimestamp(submission.created_utc).isoformat() + "Z"
                mentions.append({
                    "source": "reddit",
                    "source_url": f"https://reddit.com{submission.permalink}",
                    "title": submission.title,
                    "content": submission.selftext[:2000] if submission.selftext else submission.title,
                    "author": str(submission.author) if submission.author else None,
                    "published_at": published,
                })

            logger.info(f"[Reddit] Fetched {len(mentions)} posts")
            if mentions:
                logger.info(f"[Reddit] Sample: '{mentions[0]['title'][:80]}'")
            return mentions

        except Exception as e:
            logger.error(f"[Reddit] Fetch failed: {e}", exc_info=True)
            return []
