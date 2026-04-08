"""API Blueprint definitions"""

from flask import Blueprint

monitors_bp = Blueprint('monitors', __name__)
mentions_bp = Blueprint('mentions', __name__)
analysis_bp = Blueprint('analysis', __name__)
digests_bp = Blueprint('digests', __name__)
tasks_bp = Blueprint('tasks', __name__)
simulations_bp = Blueprint('simulations', __name__)
settings_bp = Blueprint('settings', __name__)

from . import monitors, mentions, analysis, digests, tasks, simulations, settings
