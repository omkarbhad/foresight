"""Claude-generated daily digest summaries"""

import uuid
from datetime import datetime, timedelta

from ..utils.claude_client import ClaudeClient
from ..services.trend_analyzer import get_dashboard_stats
from ..models.mention import Mention
from ..db import execute_write, execute_query, execute_one
from ..utils.logger import get_logger
import json

logger = get_logger('foresight.digest')

DIGEST_PROMPT = """Generate a daily media monitoring digest for "{monitor_name}".

Period: {period_start} to {period_end}

Stats: {stats}

Top Mentions:
{mentions_text}

Write a concise executive summary covering:
1. Overall sentiment and volume trends
2. Key stories and themes
3. Any crisis signals or risks
4. Positive coverage opportunities
5. Recommended next steps

Keep it professional and actionable, 3-5 paragraphs."""


def generate_digest(monitor_id, monitor_name):
    try:
        client = ClaudeClient()

        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=1)

        stats = get_dashboard_stats(monitor_id)
        mentions = Mention.list_by_monitor(monitor_id, limit=20)

        mentions_text = "\n".join([
            f"- [{m.source}] {m.title or 'No title'} | Sentiment: {m.sentiment_label} | Crisis: {m.crisis_score}"
            for m in mentions
        ])

        summary = client.chat(
            messages=[{
                "role": "user",
                "content": DIGEST_PROMPT.format(
                    monitor_name=monitor_name,
                    period_start=period_start.strftime('%Y-%m-%d %H:%M'),
                    period_end=period_end.strftime('%Y-%m-%d %H:%M'),
                    stats=str(stats),
                    mentions_text=mentions_text or "No mentions in this period.",
                )
            }],
            system="You are a PR communications expert writing executive briefings.",
        )

        top_ids = [m.mention_id for m in mentions[:5]]

        digest_id = f"dig_{uuid.uuid4().hex[:12]}"
        execute_write(
            """INSERT INTO digests (digest_id, monitor_id, period_start, period_end, summary, stats, top_mention_ids)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (digest_id, monitor_id, period_start, period_end, summary,
             json.dumps(stats), top_ids)
        )

        logger.info(f"Generated digest {digest_id} for {monitor_name}")
        return {"digest_id": digest_id, "summary": summary, "stats": stats}

    except Exception as e:
        logger.error(f"Digest generation failed: {e}")
        return {"error": str(e)}


def list_digests(monitor_id, limit=20):
    rows = execute_query(
        """SELECT * FROM digests WHERE monitor_id = %s ORDER BY generated_at DESC LIMIT %s""",
        (monitor_id, limit)
    )
    return [
        {
            "digest_id": r['digest_id'],
            "monitor_id": r['monitor_id'],
            "period_start": r['period_start'].isoformat() if r.get('period_start') else None,
            "period_end": r['period_end'].isoformat() if r.get('period_end') else None,
            "generated_at": r['generated_at'].isoformat() if r.get('generated_at') else None,
            "summary": r['summary'],
            "stats": r['stats'],
            "top_mention_ids": r.get('top_mention_ids') or [],
        }
        for r in (rows or [])
    ]
