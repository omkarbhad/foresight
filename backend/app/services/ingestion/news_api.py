"""NewsAPI integration"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ...config import Config
from ...utils.logger import get_logger

logger = get_logger('foresight.ingestion.news')


class NewsAPIService:
    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self):
        self.api_key = Config.NEWS_API_KEY

    @property
    def source_name(self):
        return "news"

    def fetch_mentions(self, keywords, negative_keywords=None, since=None):
        if not self.api_key:
            logger.warning("[NewsAPI] API key not configured — set NEWS_API_KEY in .env")
            return []

        query = " OR ".join(f'"{kw}"' for kw in keywords)
        if negative_keywords:
            for nk in negative_keywords:
                query += f' NOT "{nk}"'

        if not since:
            since = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

        params = {
            "q": query,
            "from": since,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 50,
            "apiKey": self.api_key,
        }

        logger.info(f"[NewsAPI] Requesting: query='{query}', since={since}")

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            logger.info(f"[NewsAPI] Response: status={resp.status_code}")

            if resp.status_code != 200:
                body = resp.text[:500]
                logger.error(f"[NewsAPI] Error response: {body}")
                return []

            data = resp.json()
            total_results = data.get("totalResults", 0)
            articles = data.get("articles", [])
            logger.info(f"[NewsAPI] totalResults={total_results}, articles returned={len(articles)}")

            if data.get("status") == "error":
                logger.error(f"[NewsAPI] API error: {data.get('code')} — {data.get('message')}")
                return []

            mentions = []
            for article in articles:
                mentions.append({
                    "source": "news",
                    "source_url": article.get("url"),
                    "title": article.get("title"),
                    "content": article.get("description") or article.get("content", ""),
                    "author": article.get("author"),
                    "published_at": article.get("publishedAt"),
                })

            logger.info(f"[NewsAPI] Parsed {len(mentions)} articles successfully")
            return mentions

        except requests.exceptions.Timeout:
            logger.error("[NewsAPI] Request timed out after 30s")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[NewsAPI] Connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"[NewsAPI] Unexpected error: {e}", exc_info=True)
            return []
