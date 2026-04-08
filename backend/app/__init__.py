"""Foresight Backend - Flask application factory"""

import os

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    logger = setup_logger('foresight')

    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("Foresight Backend starting...")
        logger.info("=" * 50)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.before_request
    def log_request():
        req_logger = get_logger('foresight.request')
        req_logger.debug(f"Request: {request.method} {request.path}")

    @app.after_request
    def log_response(response):
        req_logger = get_logger('foresight.request')
        req_logger.debug(f"Response: {response.status_code}")
        return response

    # Register blueprints
    from .api import monitors_bp, mentions_bp, analysis_bp, digests_bp, tasks_bp, simulations_bp, settings_bp
    app.register_blueprint(monitors_bp, url_prefix='/api/monitors')
    app.register_blueprint(mentions_bp, url_prefix='/api/mentions')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(digests_bp, url_prefix='/api/digests')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(simulations_bp, url_prefix='/api/simulations')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    # Initialize Neo4j graph schema (if enabled)
    if Config.GRAPH_MEMORY_ENABLED and should_log_startup:
        try:
            from .services.graph_schema import init_graph_schema, get_neo4j_driver
            driver = get_neo4j_driver()
            init_graph_schema(driver)
            logger.info("Neo4j graph schema initialized")
        except Exception as e:
            logger.warning(f"Neo4j init failed (graph memory will be disabled): {e}")

    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'Foresight Backend'}

    if should_log_startup:
        logger.info("Foresight Backend started successfully")

    return app
