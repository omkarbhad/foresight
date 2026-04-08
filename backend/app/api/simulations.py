"""PR Simulation API endpoints"""

from flask import request, jsonify
from . import simulations_bp
from ..config import Config
from ..models.simulation import Simulation
from ..services.crewai_engine import start_simulation


@simulations_bp.route('', methods=['POST'])
def create_simulation():
    # Check LLM is configured before starting
    if not Config.is_llm_configured():
        return jsonify({
            "success": False,
            "error": "No LLM provider configured. Open Settings to add an API key.",
        }), 400

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400

    scenarios = data.get('scenarios', [])
    if not scenarios or not isinstance(scenarios, list):
        return jsonify({"success": False, "error": "scenarios array required"}), 400

    scenarios = [s.strip() for s in scenarios if isinstance(s, str) and s.strip()]
    if not scenarios:
        return jsonify({"success": False, "error": "At least one non-empty scenario required"}), 400

    config = data.get('config', {})
    task_id = start_simulation(
        scenarios=scenarios,
        config=config,
    )

    return jsonify({"success": True, "task_id": task_id}), 202


@simulations_bp.route('', methods=['GET'])
def list_simulations():
    limit = int(request.args.get('limit', 10))
    sims = Simulation.list_recent(limit=limit)
    return jsonify({"success": True, "data": [s.to_dict() for s in sims]})


@simulations_bp.route('/<simulation_id>', methods=['GET'])
def get_simulation(simulation_id):
    sim = Simulation.get_by_id(simulation_id)
    if not sim:
        return jsonify({"success": False, "error": "Simulation not found"}), 404
    return jsonify({"success": True, "data": sim.to_dict()})
