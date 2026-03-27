"""Digest generation + history"""

from flask import request, jsonify
from . import digests_bp
from ..services.digest_generator import generate_digest, list_digests
from ..models.monitor import Monitor


@digests_bp.route('/generate', methods=['POST'])
def create_digest():
    data = request.get_json()
    if not data or not data.get('monitor_id'):
        return jsonify({"success": False, "error": "monitor_id required"}), 400

    monitor = Monitor.get_by_id(data['monitor_id'])
    if not monitor:
        return jsonify({"success": False, "error": "Monitor not found"}), 404

    result = generate_digest(monitor.monitor_id, monitor.name)
    return jsonify({"success": True, "data": result})


@digests_bp.route('/<monitor_id>', methods=['GET'])
def get_digests(monitor_id):
    limit = int(request.args.get('limit', 20))
    digests = list_digests(monitor_id, limit=limit)
    return jsonify({"success": True, "data": digests})
