"""Twitter/X API v2 integration"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ...config import Config
from ...utils.logger import get_logger

logger = get_logger('foresight.ingestion.twitter')


class TwitterService:
    BASE_URL = "https://api.twitter.com/2/tweets/search/recent"

    def __init__(self):
        self.bearer_token = Config.TWITTER_BEARER_TOKEN

    @property
    def source_name(self):
        return "twitter"

    def fetch_mentions(self, keywords, negative_keywords=None, since=None):
        if not self.bearer_token:
            logger.warning("[Twitter] Bearer token not configured — set TWITTER_BEARER_TOKEN in .env")
            return []

        query_parts = [f'"{kw}"' for kw in keywords]
        query = " OR ".join(query_parts)
        if negative_keywords:
            for nk in negative_keywords:
                query += f' -{nk}'
        query += " -is:retweet lang:en"

        logger.info(f"[Twitter] Searching: query='{query[:100]}', max_results=50")

        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        params = {
            "query": query,
            "max_results": 50,
            "tweet.fields": "created_at,author_id,public_metrics,text",
        }

        try:
            resp = requests.get(self.BASE_URL, headers=headers, params=params, timeout=30)
            logger.info(f"[Twitter] Response: status={resp.status_code}")

            if resp.status_code != 200:
                body = resp.text[:500]
                logger.error(f"[Twitter] Error response: {body}")
                return []

            data = resp.json()
            result_count = data.get("meta", {}).get("result_count", 0)
            logger.info(f"[Twitter] result_count={result_count}")

            mentions = []
            for tweet in data.get("data", []):
                metrics = tweet.get("public_metrics", {})
                mentions.append({
                    "source": "twitter",
                    "source_url": f"https://twitter.com/i/web/status/{tweet['id']}",
                    "title": None,
                    "content": tweet.get("text", ""),
                    "author": tweet.get("author_id"),
                    "published_at": tweet.get("created_at"),
                    "reach_estimate": metrics.get("impression_count", 0),
                })

            logger.info(f"[Twitter] Parsed {len(mentions)} tweets")
            if mentions:
                logger.info(f"[Twitter] Sample: '{mentions[0]['content'][:80]}'")
            return mentions

        except requests.exceptions.Timeout:
            logger.error("[Twitter] Request timed out after 30s")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[Twitter] Connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"[Twitter] Unexpected error: {e}", exc_info=True)
            return []
