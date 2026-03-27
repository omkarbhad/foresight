"""On-demand data ingestion for simulation startup.

Fetches fresh mentions from NewsAPI, Reddit, and Twitter for a single
monitor, deduplicates, stores, and runs Claude analysis — all synchronously
within the simulation thread so that freshly fetched data appears in the
historical briefing.
"""

from typing import Dict

from ..models.monitor import Monitor
from ..models.mention import Mention
from ..services.ingestion import NewsAPIService, RedditService, TwitterService, FinnhubService
from ..services.dedup_service import compute_content_hash, is_duplicate
from ..services.claude_analyzer import analyze_unprocessed
from ..utils.logger import get_logger

logger = get_logger('foresight.ingestion')

SOURCE_SERVICES = {
    'news': NewsAPIService,
    'reddit': RedditService,
    'twitter': TwitterService,
    'finnhub': FinnhubService,
}


def fetch_and_analyze_for_monitor(monitor_id: str) -> Dict:
    """Fetch fresh mentions from all configured APIs, store, and analyze.

    Runs synchronously. Called at simulation start before historical loading.

    Returns:
        {"fetched": int, "new": int, "analyzed": int}
    """
    monitor = Monitor.get_by_id(monitor_id)
    if not monitor:
        logger.warning(f"Monitor {monitor_id} not found for on-demand ingestion")
        return {"fetched": 0, "new": 0, "analyzed": 0}

    logger.info(f"On-demand ingestion for '{monitor.name}' (keywords: {monitor.keywords})")

    total_fetched = 0
    total_new = 0

    for source_name in (monitor.sources or ['news', 'reddit', 'twitter']):
        service_cls = SOURCE_SERVICES.get(source_name)
        if not service_cls:
            continue

        try:
            service = service_cls()
            raw_mentions = service.fetch_mentions(
                keywords=monitor.keywords,
                negative_keywords=monitor.negative_keywords,
            )
            total_fetched += len(raw_mentions)

            for raw in raw_mentions:
                content_hash = compute_content_hash(
                    raw['source'], raw.get('title'), raw.get('content')
                )
                if is_duplicate(content_hash):
                    continue

                Mention.create(
                    monitor_id=monitor.monitor_id,
                    source=raw['source'],
                    content_hash=content_hash,
                    source_url=raw.get('source_url'),
                    title=raw.get('title'),
                    content=raw.get('content'),
                    author=raw.get('author'),
                    published_at=raw.get('published_at'),
                )
                total_new += 1

            logger.info(f"  [{source_name}] {len(raw_mentions)} fetched, {total_new} new")

        except Exception as e:
            logger.error(f"  [{source_name}] failed: {e}")

    # Analyze newly ingested (unanalyzed) mentions
    total_analyzed = 0
    try:
        results = analyze_unprocessed(limit=50)
        total_analyzed = len(results)
    except Exception as e:
        logger.error(f"  Analysis failed: {e}")

    logger.info(
        f"On-demand ingestion complete: {total_fetched} fetched, "
        f"{total_new} new, {total_analyzed} analyzed"
    )

    return {"fetched": total_fetched, "new": total_new, "analyzed": total_analyzed}
