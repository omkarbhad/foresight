"""What-If prediction engine powered by Claude"""

from ..utils.claude_client import ClaudeClient
from ..services.trend_analyzer import get_sentiment_trend, get_volume_by_source, get_dashboard_stats
from ..models.mention import Mention
from ..utils.logger import get_logger

logger = get_logger('foresight.prediction')

PREDICTION_PROMPT = """You are a PR strategist and media analyst. Given the current media monitoring data for "{monitor_name}", predict what would happen if the following scenario occurs:

SCENARIO: {scenario}

CURRENT MEDIA LANDSCAPE:
- Dashboard Stats (last 7 days): {stats}
- Sentiment Trend (last 30 days): {trend}
- Volume by Source: {volume}
- Recent Mentions Sample: {recent_mentions}

Provide a detailed prediction as JSON:
{{
    "predicted_sentiment_shift": float (-1.0 to 1.0, how sentiment would change),
    "predicted_volume_change_pct": float (percentage change in mention volume),
    "crisis_probability": float (0.0-1.0),
    "timeline": "string describing expected timeline of impact",
    "key_risks": ["risk1", "risk2", ...],
    "opportunities": ["opportunity1", "opportunity2", ...],
    "recommended_actions": ["action1", "action2", ...],
    "narrative_prediction": "2-3 paragraph narrative of how events would likely unfold"
}}"""


def predict_scenario(monitor_id, monitor_name, scenario):
    try:
        client = ClaudeClient()

        stats = get_dashboard_stats(monitor_id)
        trend = get_sentiment_trend(monitor_id, days=30)
        volume = get_volume_by_source(monitor_id, days=30)

        recent = Mention.list_by_monitor(monitor_id, limit=5)
        recent_summaries = [
            {"title": m.title, "sentiment": m.sentiment_label, "source": m.source}
            for m in recent
        ]

        result = client.chat_json(
            messages=[{
                "role": "user",
                "content": PREDICTION_PROMPT.format(
                    monitor_name=monitor_name,
                    scenario=scenario,
                    stats=str(stats),
                    trend=str(trend[-7:]) if trend else "No data",
                    volume=str(volume),
                    recent_mentions=str(recent_summaries),
                )
            }],
            system="You are a world-class PR strategist. Provide realistic, data-informed predictions.",
            max_tokens=4096,
        )

        logger.info(f"What-If prediction generated for monitor {monitor_id}")
        return result

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {"error": str(e)}
