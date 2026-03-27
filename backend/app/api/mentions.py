"""Mention retrieval + filters"""

from flask import request, jsonify
from . import mentions_bp
from ..models.mention import Mention


@mentions_bp.route('/<monitor_id>', methods=['GET'])
def list_mentions(monitor_id):
    source = request.args.get('source')
    sentiment = request.args.get('sentiment')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    sort_by = request.args.get('sort_by', 'ingested_at')

    mentions = Mention.list_by_monitor(
        monitor_id, source=source, sentiment=sentiment,
        limit=limit, offset=offset, sort_by=sort_by
    )
    return jsonify({
        "success": True,
        "data": [m.to_dict() for m in mentions],
        "count": len(mentions),
    })


@mentions_bp.route('/detail/<mention_id>', methods=['GET'])
def get_mention(mention_id):
    mention = Mention.get_by_id(mention_id)
    if not mention:
        return jsonify({"success": False, "error": "Mention not found"}), 404
    return jsonify({"success": True, "data": mention.to_dict()})


@mentions_bp.route('/amplify', methods=['GET'])
def amplify_queue():
    monitor_id = request.args.get('monitor_id')
    limit = int(request.args.get('limit', 20))
    from ..services.amplify_service import get_amplify_queue
    data = get_amplify_queue(monitor_id=monitor_id, limit=limit)
    return jsonify({"success": True, "data": data})
