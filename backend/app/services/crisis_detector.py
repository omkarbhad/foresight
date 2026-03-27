"""Crisis detection - threshold-based alerting"""

from ..models.mention import Mention
from ..models.alert import AlertEvent
from ..models.monitor import Monitor
from ..utils.logger import get_logger

logger = get_logger('foresight.crisis')


def check_for_crises():
    """Scan recently analyzed mentions for crisis-level scores and create alerts."""
    monitors = Monitor.list_all(active_only=True)
    new_alerts = []

    for monitor in monitors:
        threshold = monitor.alert_threshold

        from ..db import execute_query
        rows = execute_query(
            """SELECT * FROM mentions
               WHERE monitor_id = %s AND crisis_score >= %s
               AND is_duplicate = FALSE
               AND mention_id NOT IN (
                   SELECT mention_id FROM alert_events WHERE monitor_id = %s AND mention_id IS NOT NULL
               )
               ORDER BY crisis_score DESC LIMIT 10""",
            (monitor.monitor_id, threshold, monitor.monitor_id)
        )

        for row in rows or []:
            mention = Mention.from_row(row)
            event_id = AlertEvent.create(
                monitor_id=monitor.monitor_id,
                mention_id=mention.mention_id,
                crisis_score=mention.crisis_score,
                delivered_via=['dashboard'],
            )
            new_alerts.append(event_id)
            logger.warning(f"Crisis alert for {monitor.name}: score={mention.crisis_score}, mention={mention.mention_id}")

    if new_alerts:
        logger.info(f"Created {len(new_alerts)} new crisis alerts")
    return new_alerts
