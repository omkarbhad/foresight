"""Task polling endpoint"""

from flask import request, jsonify
from . import tasks_bp
from ..models.task import TaskManager


@tasks_bp.route('/<task_id>', methods=['GET'])
def get_task(task_id):
    tm = TaskManager()
    task = tm.get_task(task_id)
    if not task:
        return jsonify({"success": False, "error": "Task not found"}), 404
    return jsonify({"success": True, "data": task.to_dict()})


@tasks_bp.route('/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    tm = TaskManager()
    success = tm.cancel_task(task_id)
    if not success:
        task = tm.get_task(task_id)
        if not task:
            return jsonify({"success": False, "error": "Task not found"}), 404
        return jsonify({"success": False, "error": f"Task cannot be cancelled (status: {task.status.value})"}), 400
    return jsonify({"success": True, "message": "Cancellation requested"})


@tasks_bp.route('', methods=['GET'])
def list_tasks():
    tm = TaskManager()
    task_type = request.args.get('type')
    tasks = tm.list_tasks(task_type=task_type)
    return jsonify({"success": True, "data": tasks})
