"""SQL-based trend computation"""

from ..db import execute_query
from ..utils.logger import get_logger

logger = get_logger('foresight.trends')


def get_sentiment_trend(monitor_id, days=30):
    rows = execute_query(
        """SELECT DATE(ingested_at) as date,
                  AVG(sentiment_score) as avg_sentiment,
                  COUNT(*) as mention_count
           FROM mentions
           WHERE monitor_id = %s AND is_duplicate = FALSE
                 AND ingested_at >= NOW() - INTERVAL '%s days'
           GROUP BY DATE(ingested_at)
           ORDER BY date""",
        (monitor_id, days)
    )
    return [
        {"date": str(r['date']), "avg_sentiment": round(r['avg_sentiment'] or 0, 3),
         "count": r['mention_count']}
        for r in (rows or [])
    ]


def get_volume_by_source(monitor_id, days=30):
    rows = execute_query(
        """SELECT source, COUNT(*) as count
           FROM mentions
           WHERE monitor_id = %s AND is_duplicate = FALSE
                 AND ingested_at >= NOW() - INTERVAL '%s days'
           GROUP BY source ORDER BY count DESC""",
        (monitor_id, days)
    )
    return [{"source": r['source'], "count": r['count']} for r in (rows or [])]


def get_top_topics(monitor_id, days=30, limit=10):
    rows = execute_query(
        """SELECT unnest(topics) as topic, COUNT(*) as count
           FROM mentions
           WHERE monitor_id = %s AND is_duplicate = FALSE
                 AND ingested_at >= NOW() - INTERVAL '%s days'
           GROUP BY topic ORDER BY count DESC LIMIT %s""",
        (monitor_id, days, limit)
    )
    return [{"topic": r['topic'], "count": r['count']} for r in (rows or [])]


def get_dashboard_stats(monitor_id):
    row = execute_query(
        """SELECT
               COUNT(*) as total_mentions,
               AVG(sentiment_score) as avg_sentiment,
               COUNT(*) FILTER (WHERE sentiment_label = 'positive') as positive_count,
               COUNT(*) FILTER (WHERE sentiment_label = 'negative') as negative_count,
               COUNT(*) FILTER (WHERE sentiment_label = 'neutral') as neutral_count,
               COUNT(*) FILTER (WHERE crisis_score >= 0.7) as crisis_count,
               COUNT(*) FILTER (WHERE amplify_worthy = TRUE) as amplify_count,
               MAX(crisis_score) as max_crisis_score
           FROM mentions
           WHERE monitor_id = %s AND is_duplicate = FALSE
                 AND ingested_at >= NOW() - INTERVAL '7 days'""",
        (monitor_id,)
    )
    if row:
        r = row[0]
        return {
            "total_mentions": r['total_mentions'],
            "avg_sentiment": round(r['avg_sentiment'] or 0, 3),
            "positive_count": r['positive_count'],
            "negative_count": r['negative_count'],
            "neutral_count": r['neutral_count'],
            "crisis_count": r['crisis_count'],
            "amplify_count": r['amplify_count'],
            "max_crisis_score": round(r['max_crisis_score'] or 0, 3),
        }
    return {}


def get_competitor_comparison(monitor_ids, days=30):
    results = []
    for mid in monitor_ids:
        row = execute_query(
            """SELECT
                   COUNT(*) as total,
                   AVG(sentiment_score) as avg_sentiment
               FROM mentions
               WHERE monitor_id = %s AND is_duplicate = FALSE
                     AND ingested_at >= NOW() - INTERVAL '%s days'""",
            (mid, days)
        )
        if row:
            r = row[0]
            results.append({
                "monitor_id": mid,
                "total_mentions": r['total'],
                "avg_sentiment": round(r['avg_sentiment'] or 0, 3),
            })
    return results
