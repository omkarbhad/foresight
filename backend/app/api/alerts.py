"""Crisis alert endpoints — enriched with monitor + mention details"""

from flask import request, jsonify
from . import alerts_bp
from ..models.alert import AlertEvent
from ..models.monitor import Monitor
from ..models.mention import Mention


def _enrich_alert(alert):
    """Add monitor name and mention details to an alert dict."""
    data = alert.to_dict()

    # Enrich with monitor name
    monitor = Monitor.get_by_id(alert.monitor_id)
    data['monitor_name'] = monitor.name if monitor else alert.monitor_id

    # Enrich with mention details
    if alert.mention_id:
        mention = Mention.get_by_id(alert.mention_id)
        if mention:
            data['mention'] = {
                'title': mention.title,
                'content': (mention.content or '')[:300],
                'source': mention.source,
                'source_url': mention.source_url,
                'author': mention.author,
                'sentiment_label': mention.sentiment_label,
                'sentiment_score': mention.sentiment_score,
                'analysis_summary': mention.analysis_summary,
                'topics': mention.topics,
                'published_at': mention.published_at,
            }
        else:
            data['mention'] = None
    else:
        data['mention'] = None

    return data


@alerts_bp.route('', methods=['GET'])
def list_alerts():
    monitor_id = request.args.get('monitor_id')
    unack = request.args.get('unacknowledged_only', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 50))

    if monitor_id:
        alerts = AlertEvent.list_by_monitor(monitor_id, unacknowledged_only=unack, limit=limit)
    else:
        alerts = AlertEvent.list_all(unacknowledged_only=unack, limit=limit)

    return jsonify({"success": True, "data": [_enrich_alert(a) for a in alerts]})


@alerts_bp.route('/<event_id>/acknowledge', methods=['POST'])
def acknowledge_alert(event_id):
    success = AlertEvent.acknowledge(event_id)
    if not success:
        return jsonify({"success": False, "error": "Alert not found"}), 404
    return jsonify({"success": True, "message": "Alert acknowledged"})
