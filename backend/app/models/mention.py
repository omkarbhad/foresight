"""Mention model - every detected brand/topic mention"""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from ..db import execute_query, execute_one, execute_write


@dataclass
class Mention:
    mention_id: str = ""
    monitor_id: str = ""
    source: str = ""
    source_url: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None
    ingested_at: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    reach_estimate: Optional[int] = None
    crisis_score: Optional[float] = None
    amplify_worthy: bool = False
    analysis_summary: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    content_hash: str = ""
    is_duplicate: bool = False

    def to_dict(self):
        return {
            "mention_id": self.mention_id,
            "monitor_id": self.monitor_id,
            "source": self.source,
            "source_url": self.source_url,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "published_at": self.published_at,
            "ingested_at": self.ingested_at,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "reach_estimate": self.reach_estimate,
            "crisis_score": self.crisis_score,
            "amplify_worthy": self.amplify_worthy,
            "analysis_summary": self.analysis_summary,
            "topics": self.topics,
            "is_duplicate": self.is_duplicate,
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            mention_id=row['mention_id'],
            monitor_id=row['monitor_id'],
            source=row['source'],
            source_url=row.get('source_url'),
            title=row.get('title'),
            content=row.get('content'),
            author=row.get('author'),
            published_at=row['published_at'].isoformat() if row.get('published_at') else None,
            ingested_at=row['ingested_at'].isoformat() if row.get('ingested_at') else None,
            sentiment_score=row.get('sentiment_score'),
            sentiment_label=row.get('sentiment_label'),
            reach_estimate=row.get('reach_estimate'),
            crisis_score=row.get('crisis_score'),
            amplify_worthy=row.get('amplify_worthy', False),
            analysis_summary=row.get('analysis_summary'),
            topics=row.get('topics') or [],
            content_hash=row.get('content_hash', ''),
            is_duplicate=row.get('is_duplicate', False),
        )

    @classmethod
    def create(cls, monitor_id, source, content_hash, **kwargs):
        mention_id = f"mnt_{uuid.uuid4().hex[:12]}"
        execute_write(
            """INSERT INTO mentions (mention_id, monitor_id, source, source_url, title, content,
               author, published_at, content_hash, is_duplicate)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (mention_id, monitor_id, source,
             kwargs.get('source_url'), kwargs.get('title'), kwargs.get('content'),
             kwargs.get('author'), kwargs.get('published_at'),
             content_hash, kwargs.get('is_duplicate', False))
        )
        return mention_id

    @classmethod
    def get_by_id(cls, mention_id):
        row = execute_one("SELECT * FROM mentions WHERE mention_id = %s", (mention_id,))
        return cls.from_row(row)

    @classmethod
    def exists_by_hash(cls, content_hash):
        row = execute_one(
            "SELECT mention_id FROM mentions WHERE content_hash = %s LIMIT 1",
            (content_hash,)
        )
        return row is not None

    @classmethod
    def list_by_monitor(cls, monitor_id, source=None, sentiment=None,
                        limit=50, offset=0, sort_by='ingested_at'):
        query = "SELECT * FROM mentions WHERE monitor_id = %s AND is_duplicate = FALSE"
        params = [monitor_id]

        if source:
            query += " AND source = %s"
            params.append(source)
        if sentiment:
            query += " AND sentiment_label = %s"
            params.append(sentiment)

        allowed_sorts = {'ingested_at', 'crisis_score', 'sentiment_score', 'published_at'}
        if sort_by not in allowed_sorts:
            sort_by = 'ingested_at'
        query += f" ORDER BY {sort_by} DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        rows = execute_query(query, tuple(params))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def list_unanalyzed(cls, limit=50):
        rows = execute_query(
            """SELECT * FROM mentions WHERE sentiment_score IS NULL
               AND is_duplicate = FALSE ORDER BY ingested_at ASC LIMIT %s""",
            (limit,)
        )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def update_analysis(cls, mention_id, sentiment_score, sentiment_label,
                        crisis_score, reach_estimate, amplify_worthy,
                        analysis_summary, topics):
        execute_write(
            """UPDATE mentions SET sentiment_score=%s, sentiment_label=%s,
               crisis_score=%s, reach_estimate=%s, amplify_worthy=%s,
               analysis_summary=%s, topics=%s
               WHERE mention_id=%s""",
            (sentiment_score, sentiment_label, crisis_score, reach_estimate,
             amplify_worthy, analysis_summary, topics, mention_id)
        )

    @classmethod
    def list_amplify_worthy(cls, monitor_id=None, limit=20):
        query = "SELECT * FROM mentions WHERE amplify_worthy = TRUE AND is_duplicate = FALSE"
        params = []
        if monitor_id:
            query += " AND monitor_id = %s"
            params.append(monitor_id)
        query += " ORDER BY ingested_at DESC LIMIT %s"
        params.append(limit)
        rows = execute_query(query, tuple(params))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def count_by_monitor(cls, monitor_id):
        row = execute_one(
            "SELECT COUNT(*) as cnt FROM mentions WHERE monitor_id = %s AND is_duplicate = FALSE",
            (monitor_id,)
        )
        return row['cnt'] if row else 0
