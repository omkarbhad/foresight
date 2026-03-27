"""Alert event model"""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from ..db import execute_query, execute_one, execute_write


@dataclass
class AlertEvent:
    event_id: str = ""
    monitor_id: str = ""
    mention_id: Optional[str] = None
    crisis_score: float = 0.0
    delivered_via: List[str] = field(default_factory=list)
    delivered_at: Optional[str] = None
    acknowledged: bool = False

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "monitor_id": self.monitor_id,
            "mention_id": self.mention_id,
            "crisis_score": self.crisis_score,
            "delivered_via": self.delivered_via,
            "delivered_at": self.delivered_at,
            "acknowledged": self.acknowledged,
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            event_id=row['event_id'],
            monitor_id=row['monitor_id'],
            mention_id=row.get('mention_id'),
            crisis_score=row.get('crisis_score', 0.0),
            delivered_via=row.get('delivered_via') or [],
            delivered_at=row['delivered_at'].isoformat() if row.get('delivered_at') else None,
            acknowledged=row.get('acknowledged', False),
        )

    @classmethod
    def create(cls, monitor_id, mention_id, crisis_score, delivered_via=None):
        event_id = f"alert_{uuid.uuid4().hex[:12]}"
        execute_write(
            """INSERT INTO alert_events (event_id, monitor_id, mention_id, crisis_score, delivered_via)
               VALUES (%s, %s, %s, %s, %s)""",
            (event_id, monitor_id, mention_id, crisis_score, delivered_via or [])
        )
        return event_id

    @classmethod
    def list_by_monitor(cls, monitor_id, unacknowledged_only=False, limit=50):
        query = "SELECT * FROM alert_events WHERE monitor_id = %s"
        params = [monitor_id]
        if unacknowledged_only:
            query += " AND acknowledged = FALSE"
        query += " ORDER BY delivered_at DESC LIMIT %s"
        params.append(limit)
        rows = execute_query(query, tuple(params))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def list_all(cls, unacknowledged_only=False, limit=50):
        query = "SELECT * FROM alert_events"
        params = []
        if unacknowledged_only:
            query += " WHERE acknowledged = FALSE"
        query += " ORDER BY delivered_at DESC LIMIT %s"
        params.append(limit)
        rows = execute_query(query, tuple(params))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def acknowledge(cls, event_id):
        return execute_write(
            "UPDATE alert_events SET acknowledged = TRUE WHERE event_id = %s",
            (event_id,)
        ) > 0
