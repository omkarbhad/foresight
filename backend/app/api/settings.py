"""Settings API — manage API keys and configuration."""

from flask import request, jsonify
from . import settings_bp
from ..db import execute_query, execute_write
from ..config import invalidate_settings_cache


VALID_KEYS = {
    "llm_provider", "llm_model", "llm_api_key",
    "news_api_key", "reddit_client_id", "reddit_client_secret",
    "finnhub_api_key", "twitter_bearer_token",
}

SECRET_KEYS = {
    "llm_api_key", "news_api_key", "reddit_client_secret",
    "finnhub_api_key", "twitter_bearer_token",
}


def _mask_value(key: str, value: str) -> str:
    if key not in SECRET_KEYS or not value or len(value) < 8:
        return value
    return value[:4] + "***...***" + value[-3:]


@settings_bp.route('', methods=['GET'])
def list_settings():
    rows = execute_query("SELECT key, value FROM settings") or []
    result = {}
    for row in rows:
        k, v = row["key"], row["value"]
        if k in VALID_KEYS:
            result[k] = _mask_value(k, v)
    return jsonify({"success": True, "data": result})


@settings_bp.route('', methods=['PUT'])
def update_settings():
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "error": "JSON object required"}), 400

    updated = 0
    for key, value in data.items():
        if key not in VALID_KEYS:
            continue
        if not isinstance(value, str):
            continue
        if "***...***" in value:
            continue

        execute_write(
            """INSERT INTO settings (key, value, updated_at)
               VALUES (%s, %s, NOW())
               ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()""",
            (key, value, value),
        )
        updated += 1

    invalidate_settings_cache()
    return jsonify({"success": True, "updated": updated})


@settings_bp.route('/status', methods=['GET'])
def settings_status():
    from ..config import Config

    status = {}
    for key in VALID_KEYS:
        val = Config.get(key)
        status[key] = bool(val)

    status["llm_configured"] = status.get("llm_api_key", False)

    return jsonify({"success": True, "data": status})
