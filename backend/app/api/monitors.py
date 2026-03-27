"""Monitor CRUD endpoints"""

from flask import request, jsonify
from . import monitors_bp
from ..models.monitor import Monitor


@monitors_bp.route('', methods=['GET'])
def list_monitors():
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    monitors = Monitor.list_all(active_only=active_only)
    return jsonify({"success": True, "data": [m.to_dict() for m in monitors]})


@monitors_bp.route('/<monitor_id>', methods=['GET'])
def get_monitor(monitor_id):
    monitor = Monitor.get_by_id(monitor_id)
    if not monitor:
        return jsonify({"success": False, "error": "Monitor not found"}), 404
    return jsonify({"success": True, "data": monitor.to_dict()})


@monitors_bp.route('', methods=['POST'])
def create_monitor():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('keywords'):
        return jsonify({"success": False, "error": "name and keywords are required"}), 400

    monitor = Monitor.create(
        name=data['name'],
        keywords=data['keywords'],
        negative_keywords=data.get('negative_keywords', []),
        sources=data.get('sources', ['news', 'reddit', 'twitter']),
        alert_threshold=data.get('alert_threshold', 0.7),
        competitors=data.get('competitors', []),
    )
    return jsonify({"success": True, "data": monitor.to_dict()}), 201


@monitors_bp.route('/<monitor_id>', methods=['PUT'])
def update_monitor(monitor_id):
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    monitor = Monitor.update(monitor_id, **data)
    if not monitor:
        return jsonify({"success": False, "error": "Monitor not found"}), 404
    return jsonify({"success": True, "data": monitor.to_dict()})


@monitors_bp.route('/<monitor_id>', methods=['DELETE'])
def delete_monitor(monitor_id):
    deleted = Monitor.delete(monitor_id)
    if not deleted:
        return jsonify({"success": False, "error": "Monitor not found"}), 404
    return jsonify({"success": True, "message": "Monitor deleted"})
