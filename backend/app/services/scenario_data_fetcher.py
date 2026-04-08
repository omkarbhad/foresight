"""Scenario-based data fetching and sentiment analysis.

Extracts keywords from scenario text, fetches relevant data from
NewsAPI/Reddit/Twitter/Finnhub, runs sentiment analysis via Claude,
and returns a structured briefing with positive/negative breakdown.
"""

from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.llm_client import get_llm_client
from ..utils.logger import get_logger
from .ingestion import NewsAPIService, RedditService, TwitterService, FinnhubService

logger = get_logger('foresight.scenario_fetcher')

MAX_ITEMS_PER_SOURCE = 20

KEYWORD_EXTRACTION_PROMPT = """Extract 3-6 concise search keywords from this scenario that would
be effective for querying news APIs, Reddit, Twitter, and financial news services.

Scenario: {scenario}

Return JSON:
{{
    "keywords": ["keyword1", "keyword2", ...],
    "financial_entities": ["company or ticker if relevant", ...]
}}

Keywords should be short (1-3 words), specific, and capture the core actors and events.
financial_entities should list any companies, stock tickers, or market sectors mentioned or implied.
Return empty financial_entities array if none are relevant."""

SENTIMENT_ANALYSIS_PROMPT = """Analyze the following collection of media data fetched for the scenario: "{scenario}"

DATA:
{data_summary}

Produce a structured sentiment analysis as JSON:
{{
    "overall_sentiment": float (-1.0 to 1.0),
    "positive_signals": ["signal1", "signal2", ...],
    "negative_signals": ["signal1", "signal2", ...],
    "neutral_observations": ["observation1", ...],
    "source_breakdown": {{
        "news": {{"sentiment": float, "volume": int, "key_themes": []}},
        "reddit": {{"sentiment": float, "volume": int, "key_themes": []}},
        "twitter": {{"sentiment": float, "volume": int, "key_themes": []}},
        "financial": {{"sentiment": float, "volume": int, "key_themes": []}}
    }},
    "summary": "2-3 sentence summary of the current media landscape for this scenario"
}}"""


def extract_keywords(scenario: str) -> Dict:
    """Use Claude to extract search keywords from a scenario description."""
    try:
        client = get_llm_client()
        result = client.chat_json(
            messages=[{
                "role": "user",
                "content": KEYWORD_EXTRACTION_PROMPT.format(scenario=scenario),
            }],
            system="You are a search query optimization expert. Extract precise, effective keywords.",
            temperature=0.2,
            max_tokens=512,
        )
        keywords = result.get("keywords", [])
        financial = result.get("financial_entities", [])
        if not keywords:
            keywords = _fallback_keyword_extraction(scenario)
        logger.info(f"Extracted keywords for scenario: {keywords}, financial: {financial}")
        return {"keywords": keywords, "financial_entities": financial}
    except Exception as e:
        logger.warning(f"Claude keyword extraction failed, using fallback: {e}")
        return {
            "keywords": _fallback_keyword_extraction(scenario),
            "financial_entities": [],
        }


def _fallback_keyword_extraction(scenario: str) -> List[str]:
    """Simple stopword-based keyword extraction as fallback."""
    import re
    stop = {
        "the", "a", "an", "is", "was", "are", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "that", "this", "with", "by",
        "from", "has", "had", "be", "been", "will", "would", "could",
        "should", "about", "into", "its", "their", "they", "it", "as",
        "not", "but", "if", "then", "than", "so", "just", "more",
    }
    words = re.findall(r"[A-Za-z']+", scenario)
    meaningful = [w for w in words if w.lower() not in stop and len(w) > 2]
    seen = set()
    unique = []
    for w in meaningful:
        low = w.lower()
        if low not in seen:
            seen.add(low)
            unique.append(w)
    return unique[:5]


def fetch_scenario_data(scenario: str) -> Dict:
    """Fetch real-world data for a scenario from all API sources.

    Returns a dict with raw data per source and a combined briefing.
    """
    kw_result = extract_keywords(scenario)
    keywords = kw_result["keywords"]
    financial_entities = kw_result["financial_entities"]

    data = {
        "news": [],
        "reddit": [],
        "twitter": [],
        "finnhub": [],
        "quotes": [],
        "keywords_used": keywords,
    }

    fetchers = {
        "news": lambda: _fetch_news(keywords),
        "reddit": lambda: _fetch_reddit(keywords),
        "twitter": lambda: _fetch_twitter(keywords),
        "finnhub": lambda: _fetch_finnhub(keywords, financial_entities),
    }

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(fn): source
            for source, fn in fetchers.items()
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                result = future.result()
                if source == "finnhub" and isinstance(result, dict):
                    data["finnhub"] = result.get("articles", [])
                    data["quotes"] = result.get("quotes", [])
                else:
                    data[source] = result
            except Exception as e:
                logger.warning(f"Fetch {source} failed for scenario: {e}")

    total = sum(len(data[s]) for s in ("news", "reddit", "twitter", "finnhub"))
    logger.info(f"Scenario data fetch complete: {total} items across all sources")

    return data


def analyze_scenario_sentiment(scenario: str, data: Dict) -> Dict:
    """Run Claude sentiment analysis on the fetched scenario data."""
    summary = _build_data_summary(data)

    if not summary.strip():
        return {
            "overall_sentiment": 0.0,
            "positive_signals": [],
            "negative_signals": [],
            "neutral_observations": ["No data available from external sources"],
            "source_breakdown": {},
            "summary": "No external data was available for analysis.",
        }

    try:
        client = get_llm_client()
        result = client.chat_json(
            messages=[{
                "role": "user",
                "content": SENTIMENT_ANALYSIS_PROMPT.format(
                    scenario=scenario,
                    data_summary=summary[:8000],
                ),
            }],
            system="You are a media sentiment analyst. Provide balanced, data-driven analysis.",
            temperature=0.3,
            max_tokens=2048,
        )
        result.setdefault("overall_sentiment", 0.0)
        result.setdefault("positive_signals", [])
        result.setdefault("negative_signals", [])
        return result
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {
            "overall_sentiment": 0.0,
            "positive_signals": [],
            "negative_signals": [],
            "neutral_observations": [],
            "source_breakdown": {},
            "summary": f"Sentiment analysis could not be completed: {e}",
        }


def build_scenario_briefing(scenario: str, data: Dict, sentiment: Dict) -> str:
    """Assemble a structured text briefing from fetched data and sentiment analysis."""
    sections = []

    sections.append(f"=== SCENARIO ANALYSIS: {scenario} ===")

    overall = sentiment.get("overall_sentiment", 0.0)
    label = "Positive" if overall > 0.2 else "Negative" if overall < -0.2 else "Neutral"
    sections.append(
        f"\nOverall Sentiment: {overall:.2f} ({label})"
    )

    pos = sentiment.get("positive_signals", [])
    if pos:
        sections.append("\nPositive Signals:")
        for s in pos[:5]:
            sections.append(f"  + {s}")

    neg = sentiment.get("negative_signals", [])
    if neg:
        sections.append("\nNegative Signals:")
        for s in neg[:5]:
            sections.append(f"  - {s}")

    summary_text = sentiment.get("summary", "")
    if summary_text:
        sections.append(f"\nMedia Landscape Summary:\n  {summary_text}")

    news = data.get("news", [])
    if news:
        sections.append(f"\n=== NEWS COVERAGE ({len(news)} articles) ===")
        for a in news[:8]:
            title = a.get("title", "")
            content = a.get("content", "")
            sections.append(f"  - {title}")
            if content:
                sections.append(f"    {content[:200]}")

    reddit = data.get("reddit", [])
    if reddit:
        sections.append(f"\n=== REDDIT DISCUSSIONS ({len(reddit)} posts) ===")
        for p in reddit[:6]:
            title = p.get("title", "")
            content = p.get("content", "")
            sections.append(f"  - {title}")
            if content:
                sections.append(f"    {content[:200]}")

    twitter = data.get("twitter", [])
    if twitter:
        sections.append(f"\n=== TWITTER/X ({len(twitter)} tweets) ===")
        for t in twitter[:5]:
            sections.append(f"  - {t.get('content', '')[:200]}")

    finnhub = data.get("finnhub", [])
    if finnhub:
        sections.append(f"\n=== FINANCIAL NEWS ({len(finnhub)} articles) ===")
        for a in finnhub[:5]:
            sections.append(f"  - {a.get('title', '')}")
            if a.get("content"):
                sections.append(f"    {a['content'][:200]}")

    quotes = data.get("quotes", [])
    if quotes:
        sections.append("\n=== MARKET DATA ===")
        for q in quotes:
            if q:
                sections.append(
                    f"  {q.get('symbol', 'N/A')}: ${q.get('current_price', 'N/A')} "
                    f"({q.get('percent_change', 'N/A')}%)"
                )

    return "\n".join(sections)


def _build_data_summary(data: Dict) -> str:
    """Build a text summary of all fetched data for sentiment analysis."""
    parts = []

    news = data.get("news", [])
    if news:
        parts.append(f"NEWS ({len(news)} articles):")
        for a in news[:10]:
            parts.append(f"  Title: {a.get('title', '')}")
            if a.get("content"):
                parts.append(f"  Content: {a['content'][:300]}")
            parts.append("")

    reddit = data.get("reddit", [])
    if reddit:
        parts.append(f"REDDIT ({len(reddit)} posts):")
        for p in reddit[:8]:
            parts.append(f"  Title: {p.get('title', '')}")
            if p.get("content"):
                parts.append(f"  Content: {p['content'][:300]}")
            parts.append("")

    twitter = data.get("twitter", [])
    if twitter:
        parts.append(f"TWITTER ({len(twitter)} tweets):")
        for t in twitter[:8]:
            parts.append(f"  {t.get('content', '')[:280]}")
        parts.append("")

    finnhub = data.get("finnhub", [])
    if finnhub:
        parts.append(f"FINANCIAL ({len(finnhub)} articles):")
        for a in finnhub[:8]:
            parts.append(f"  Title: {a.get('title', '')}")
            if a.get("content"):
                parts.append(f"  Content: {a['content'][:300]}")
            parts.append("")

    return "\n".join(parts)


def _fetch_news(keywords: List[str]) -> List[Dict]:
    try:
        svc = NewsAPIService()
        mentions = svc.fetch_mentions(keywords=keywords)
        return [
            {
                "title": m.get("title", ""),
                "content": (m.get("content") or "")[:500],
                "source_url": m.get("source_url", ""),
                "published_at": m.get("published_at", ""),
            }
            for m in mentions[:MAX_ITEMS_PER_SOURCE]
        ]
    except Exception as e:
        logger.warning(f"NewsAPI fetch failed: {e}")
        return []


def _fetch_reddit(keywords: List[str]) -> List[Dict]:
    try:
        svc = RedditService()
        mentions = svc.fetch_mentions(keywords=keywords)
        return [
            {
                "title": m.get("title", ""),
                "content": (m.get("content") or "")[:500],
                "source_url": m.get("source_url", ""),
            }
            for m in mentions[:MAX_ITEMS_PER_SOURCE]
        ]
    except Exception as e:
        logger.warning(f"Reddit fetch failed: {e}")
        return []


def _fetch_twitter(keywords: List[str]) -> List[Dict]:
    try:
        svc = TwitterService()
        mentions = svc.fetch_mentions(keywords=keywords)
        return [
            {
                "content": (m.get("content") or "")[:280],
                "source_url": m.get("source_url", ""),
            }
            for m in mentions[:MAX_ITEMS_PER_SOURCE]
        ]
    except Exception as e:
        logger.warning(f"Twitter fetch failed: {e}")
        return []


def _fetch_finnhub(keywords: List[str], financial_entities: List[str]) -> Dict:
    try:
        svc = FinnhubService()
        articles = svc.fetch_mentions(keywords=keywords)
        articles_data = [
            {
                "title": a.get("title", ""),
                "content": (a.get("content") or "")[:300],
                "source": a.get("author", ""),
            }
            for a in articles[:MAX_ITEMS_PER_SOURCE]
        ]

        quotes = []
        for entity in (financial_entities or [])[:3]:
            symbols = svc.search_symbol(entity)
            if symbols:
                quote = svc.fetch_quote(symbols[0].get("symbol", ""))
                if quote:
                    quotes.append(quote)

        return {"articles": articles_data, "quotes": quotes}
    except Exception as e:
        logger.warning(f"Finnhub fetch failed: {e}")
        return {"articles": [], "quotes": []}
