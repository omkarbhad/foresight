"""Trends, summary, and what-if endpoints"""

from flask import request, jsonify
from . import analysis_bp
from ..services import trend_analyzer
from ..services.prediction_engine import predict_scenario
from ..models.monitor import Monitor


@analysis_bp.route('/trends/<monitor_id>', methods=['GET'])
def get_trends(monitor_id):
    days = int(request.args.get('days', 30))
    return jsonify({
        "success": True,
        "data": {
            "sentiment_trend": trend_analyzer.get_sentiment_trend(monitor_id, days),
            "volume_by_source": trend_analyzer.get_volume_by_source(monitor_id, days),
            "top_topics": trend_analyzer.get_top_topics(monitor_id, days),
        }
    })


@analysis_bp.route('/dashboard/<monitor_id>', methods=['GET'])
def get_dashboard(monitor_id):
    stats = trend_analyzer.get_dashboard_stats(monitor_id)
    return jsonify({"success": True, "data": stats})


@analysis_bp.route('/competitors', methods=['GET'])
def compare_competitors():
    monitor_ids = request.args.getlist('monitor_ids')
    days = int(request.args.get('days', 30))
    data = trend_analyzer.get_competitor_comparison(monitor_ids, days)
    return jsonify({"success": True, "data": data})


@analysis_bp.route('/whatif', methods=['POST'])
def what_if():
    data = request.get_json()
    if not data or not data.get('monitor_id') or not data.get('scenario'):
        return jsonify({"success": False, "error": "monitor_id and scenario required"}), 400

    monitor = Monitor.get_by_id(data['monitor_id'])
    if not monitor:
        return jsonify({"success": False, "error": "Monitor not found"}), 404

    result = predict_scenario(
        monitor_id=monitor.monitor_id,
        monitor_name=monitor.name,
        scenario=data['scenario'],
    )
    return jsonify({"success": True, "data": result})
