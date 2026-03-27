"""Monitor model - brands/people/topics to track"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..db import execute_query, execute_one, execute_write


@dataclass
class Monitor:
    monitor_id: str = ""
    name: str = ""
    keywords: List[str] = field(default_factory=list)
    negative_keywords: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=lambda: ['news', 'reddit', 'twitter'])
    alert_threshold: float = 0.7
    competitors: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return {
            "monitor_id": self.monitor_id,
            "name": self.name,
            "keywords": self.keywords,
            "negative_keywords": self.negative_keywords,
            "sources": self.sources,
            "alert_threshold": self.alert_threshold,
            "competitors": self.competitors,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            monitor_id=row['monitor_id'],
            name=row['name'],
            keywords=row['keywords'] or [],
            negative_keywords=row['negative_keywords'] or [],
            sources=row['sources'] or [],
            alert_threshold=row['alert_threshold'],
            competitors=row['competitors'] or [],
            is_active=row['is_active'],
            created_at=row['created_at'].isoformat() if row.get('created_at') else None,
            updated_at=row['updated_at'].isoformat() if row.get('updated_at') else None,
        )

    @classmethod
    def create(cls, name, keywords, negative_keywords=None, sources=None,
               alert_threshold=0.7, competitors=None):
        monitor_id = f"mon_{uuid.uuid4().hex[:12]}"
        execute_write(
            """INSERT INTO monitors (monitor_id, name, keywords, negative_keywords, sources,
               alert_threshold, competitors)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (monitor_id, name, keywords, negative_keywords or [],
             sources or ['news', 'reddit', 'twitter'], alert_threshold, competitors or [])
        )
        return cls.get_by_id(monitor_id)

    @classmethod
    def get_by_id(cls, monitor_id):
        row = execute_one("SELECT * FROM monitors WHERE monitor_id = %s", (monitor_id,))
        return cls.from_row(row)

    @classmethod
    def list_all(cls, active_only=False):
        query = "SELECT * FROM monitors"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY created_at DESC"
        rows = execute_query(query)
        return [cls.from_row(r) for r in rows]

    @classmethod
    def update(cls, monitor_id, **kwargs):
        allowed = ['name', 'keywords', 'negative_keywords', 'sources',
                    'alert_threshold', 'competitors', 'is_active']
        sets = []
        values = []
        for k, v in kwargs.items():
            if k in allowed:
                sets.append(f"{k} = %s")
                values.append(v)
        if not sets:
            return cls.get_by_id(monitor_id)
        sets.append("updated_at = NOW()")
        values.append(monitor_id)
        execute_write(
            f"UPDATE monitors SET {', '.join(sets)} WHERE monitor_id = %s",
            tuple(values)
        )
        return cls.get_by_id(monitor_id)

    @classmethod
    def delete(cls, monitor_id):
        return execute_write("DELETE FROM monitors WHERE monitor_id = %s", (monitor_id,)) > 0
