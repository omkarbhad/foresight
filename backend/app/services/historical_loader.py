"""90-day historical data loading for simulation agents.

Queries DB for a monitor's recent history and assembles a structured
text briefing (~2000 tokens) that agents access via CrewAI tool.
"""

from typing import Dict, Optional

from ..db import execute_query, execute_one
from ..services.trend_analyzer import get_top_topics, get_volume_by_source
from ..utils.logger import get_logger

logger = get_logger('foresight.simulation')

DAYS_WINDOW = 90


def build_media_landscape_briefing(monitor_id: str) -> str:
    """Load 90-day historical data and assemble a structured text briefing."""
    sections = []

    # 1. Aggregate stats
    agg = _get_aggregate_stats(monitor_id)
    if agg:
        sections.append(
            "=== MEDIA LANDSCAPE (Last 90 Days) ===\n"
            f"Total mentions: {agg['total_mentions']}\n"
            f"Average sentiment: {agg['avg_sentiment']:.3f}\n"
            f"Crisis events (score >= 0.7): {agg['crisis_count']}\n"
            f"Peak crisis score: {agg['max_crisis_score']:.2f}\n"
            f"Positive: {agg['positive_count']} | Negative: {agg['negative_count']} | Neutral: {agg['neutral_count']}"
        )

    # 2. Weekly trend
    weekly = _get_weekly_trend(monitor_id)
    if weekly:
        trend_lines = []
        for w in weekly:
            trend_lines.append(
                f"  {w['week']}: sentiment={w['avg_sentiment']:.2f}, volume={w['count']}"
            )
        sections.append(
            "=== WEEKLY TREND ===\n" + "\n".join(trend_lines)
        )

    # 3. Notable mentions (top 50 by crisis_score or reach)
    notable = _get_notable_mentions(monitor_id)
    if notable:
        mention_lines = []
        for m in notable[:20]:  # Cap at 20 for token budget
            topics_str = ", ".join(m['topics']) if m.get('topics') else ""
            mention_lines.append(
                f"  [{m['source']}] \"{m['title'] or 'Untitled'}\" "
                f"(sentiment: {m['sentiment_score']:.2f}, "
                f"crisis: {m['crisis_score']:.2f}"
                f"{', topics: ' + topics_str if topics_str else ''})"
            )
        sections.append(
            "=== NOTABLE MENTIONS ===\n" + "\n".join(mention_lines)
        )

    # 4. Top topics
    try:
        topics = get_top_topics(monitor_id, days=DAYS_WINDOW, limit=15)
        if topics:
            topic_lines = [f"  {t['topic']} ({t['count']} mentions)" for t in topics]
            sections.append(
                "=== TOP TOPICS ===\n" + "\n".join(topic_lines)
            )
    except Exception as e:
        logger.warning(f"Failed to load topics for {monitor_id}: {e}")

    # 5. Source distribution
    try:
        sources = get_volume_by_source(monitor_id, days=DAYS_WINDOW)
        if sources:
            source_lines = [f"  {s['source']}: {s['count']} mentions" for s in sources]
            sections.append(
                "=== SOURCE DISTRIBUTION ===\n" + "\n".join(source_lines)
            )
    except Exception as e:
        logger.warning(f"Failed to load source distribution for {monitor_id}: {e}")

    if not sections:
        return "No historical data available for this monitor."

    return "\n\n".join(sections)


def _get_aggregate_stats(monitor_id: str) -> Optional[Dict]:
    """Aggregate stats over 90-day window."""
    try:
        row = execute_one(
            """SELECT
                   COUNT(*) as total_mentions,
                   AVG(sentiment_score) as avg_sentiment,
                   COUNT(*) FILTER (WHERE sentiment_label = 'positive') as positive_count,
                   COUNT(*) FILTER (WHERE sentiment_label = 'negative') as negative_count,
                   COUNT(*) FILTER (WHERE sentiment_label = 'neutral') as neutral_count,
                   COUNT(*) FILTER (WHERE crisis_score >= 0.7) as crisis_count,
                   COALESCE(MAX(crisis_score), 0) as max_crisis_score
               FROM mentions
               WHERE monitor_id = %s AND is_duplicate = FALSE
                     AND ingested_at >= NOW() - INTERVAL '90 days'""",
            (monitor_id,)
        )
        if row and row['total_mentions'] > 0:
            return {
                "total_mentions": row['total_mentions'],
                "avg_sentiment": round(float(row['avg_sentiment'] or 0), 3),
                "positive_count": row['positive_count'],
                "negative_count": row['negative_count'],
                "neutral_count": row['neutral_count'],
                "crisis_count": row['crisis_count'],
                "max_crisis_score": round(float(row['max_crisis_score'] or 0), 2),
            }
    except Exception as e:
        logger.warning(f"Failed to load aggregate stats for {monitor_id}: {e}")
    return None


def _get_weekly_trend(monitor_id: str) -> list:
    """Sentiment + volume per week over 90 days (12-13 data points)."""
    try:
        rows = execute_query(
            """SELECT DATE_TRUNC('week', ingested_at) as week,
                      AVG(sentiment_score) as avg_sentiment,
                      COUNT(*) as count
               FROM mentions
               WHERE monitor_id = %s AND is_duplicate = FALSE
                     AND ingested_at >= NOW() - INTERVAL '90 days'
               GROUP BY DATE_TRUNC('week', ingested_at)
               ORDER BY week""",
            (monitor_id,)
        )
        return [
            {
                "week": str(r['week'].date()) if hasattr(r['week'], 'date') else str(r['week']),
                "avg_sentiment": round(float(r['avg_sentiment'] or 0), 2),
                "count": r['count'],
            }
            for r in (rows or [])
        ]
    except Exception as e:
        logger.warning(f"Failed to load weekly trend for {monitor_id}: {e}")
        return []


def _get_notable_mentions(monitor_id: str) -> list:
    """Top 50 mentions by crisis_score or reach_estimate."""
    try:
        rows = execute_query(
            """SELECT title, content, source, sentiment_score, crisis_score,
                      reach_estimate, topics
               FROM mentions
               WHERE monitor_id = %s AND is_duplicate = FALSE
                     AND ingested_at >= NOW() - INTERVAL '90 days'
               ORDER BY GREATEST(COALESCE(crisis_score, 0), COALESCE(reach_estimate, 0)::float / 1000000) DESC
               LIMIT 50""",
            (monitor_id,)
        )
        return [
            {
                "title": r.get('title', ''),
                "source": r.get('source', ''),
                "sentiment_score": round(float(r.get('sentiment_score') or 0), 2),
                "crisis_score": round(float(r.get('crisis_score') or 0), 2),
                "topics": r.get('topics') or [],
            }
            for r in (rows or [])
        ]
    except Exception as e:
        logger.warning(f"Failed to load notable mentions for {monitor_id}: {e}")
        return []
