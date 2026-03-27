"""Finnhub.io stock market data integration"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ...config import Config
from ...utils.logger import get_logger

logger = get_logger('foresight.ingestion.finnhub')

BASE_URL = "https://finnhub.io/api/v1"


class FinnhubService:
    def __init__(self):
        self.api_key = Config.FINNHUB_API_KEY

    @property
    def source_name(self):
        return "finnhub"

    def fetch_mentions(self, keywords, negative_keywords=None, since=None):
        """Fetch market news and company news matching keywords.

        For each keyword, attempts symbol lookup and fetches company news.
        Also fetches general market news.
        """
        if not self.api_key:
            logger.warning("[Finnhub] API key not configured — set FINNHUB_API_KEY in .env")
            return []

        if not since:
            since = (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%d')
        elif 'T' in since:
            since = since[:10]

        to_date = datetime.utcnow().strftime('%Y-%m-%d')
        mentions = []

        market_news = self._fetch_market_news()
        for article in market_news:
            headline = article.get("headline", "")
            if keywords and not any(kw.lower() in headline.lower() for kw in keywords):
                continue
            if negative_keywords and any(nk.lower() in headline.lower() for nk in negative_keywords):
                continue
            mentions.append(self._article_to_mention(article))

        for kw in (keywords or []):
            symbols = self.search_symbol(kw)
            for sym_info in symbols[:2]:
                symbol = sym_info.get("symbol", "")
                if not symbol:
                    continue
                company_articles = self._fetch_company_news(symbol, since, to_date)
                for article in company_articles[:10]:
                    if negative_keywords and any(
                        nk.lower() in article.get("headline", "").lower()
                        for nk in negative_keywords
                    ):
                        continue
                    mentions.append(self._article_to_mention(article, symbol=symbol))

        logger.info(f"[Finnhub] Fetched {len(mentions)} mentions for keywords={keywords}")
        return mentions

    def search_symbol(self, query: str) -> List[Dict]:
        """Resolve entity/company name to ticker symbols."""
        if not self.api_key:
            return []
        try:
            resp = requests.get(
                f"{BASE_URL}/search",
                params={"q": query, "token": self.api_key},
                timeout=10,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = data.get("result", [])
            us_results = [r for r in results if r.get("type") == "Common Stock"]
            return us_results[:5] if us_results else results[:5]
        except Exception as e:
            logger.warning(f"[Finnhub] Symbol search failed for '{query}': {e}")
            return []

    def fetch_quote(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time stock quote for a symbol."""
        if not self.api_key:
            return None
        try:
            resp = requests.get(
                f"{BASE_URL}/quote",
                params={"symbol": symbol, "token": self.api_key},
                timeout=10,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if data.get("c", 0) == 0:
                return None
            return {
                "symbol": symbol,
                "current_price": data.get("c"),
                "change": data.get("d"),
                "percent_change": data.get("dp"),
                "high": data.get("h"),
                "low": data.get("l"),
                "open": data.get("o"),
                "previous_close": data.get("pc"),
            }
        except Exception as e:
            logger.warning(f"[Finnhub] Quote fetch failed for {symbol}: {e}")
            return None

    def _fetch_market_news(self, category: str = "general") -> List[Dict]:
        try:
            resp = requests.get(
                f"{BASE_URL}/news",
                params={"category": category, "token": self.api_key},
                timeout=15,
            )
            if resp.status_code != 200:
                return []
            return resp.json()[:20]
        except Exception as e:
            logger.warning(f"[Finnhub] Market news fetch failed: {e}")
            return []

    def _fetch_company_news(self, symbol: str, from_date: str, to_date: str) -> List[Dict]:
        try:
            resp = requests.get(
                f"{BASE_URL}/company-news",
                params={
                    "symbol": symbol,
                    "from": from_date,
                    "to": to_date,
                    "token": self.api_key,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                return []
            return resp.json()[:15]
        except Exception as e:
            logger.warning(f"[Finnhub] Company news fetch failed for {symbol}: {e}")
            return []

    @staticmethod
    def _article_to_mention(article: Dict, symbol: str = None) -> Dict:
        published = article.get("datetime")
        if isinstance(published, (int, float)):
            published = datetime.utcfromtimestamp(published).isoformat()

        source_label = "finnhub"
        if symbol:
            source_label = f"finnhub:{symbol}"

        return {
            "source": source_label,
            "source_url": article.get("url", ""),
            "title": article.get("headline", ""),
            "content": article.get("summary", ""),
            "author": article.get("source", ""),
            "published_at": published,
        }
