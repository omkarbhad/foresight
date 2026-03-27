"""Multi-agent PR Simulation Engine

Orchestrates Claude-powered persona agents across simulated rounds,
tracking sentiment shifts, crisis cascades, and narrative evolution.
"""

import uuid
import threading
import copy
from typing import Dict, List, Any, Optional

from ..utils.claude_client import ClaudeClient
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
from ..models.monitor import Monitor
from ..models.simulation import Simulation
from ..services.simulation_personas import PERSONAS, TIME_LABELS, DEFAULT_ROUNDS
from ..services.trend_analyzer import get_dashboard_stats

logger = get_logger('foresight.simulation')


def start_simulation(monitor_id: str, scenario: str, config: Dict = None) -> str:
    """Create a task and launch simulation in a background thread. Returns task_id."""
    tm = TaskManager()
    config = config or {}
    total_rounds = min(max(config.get('total_rounds', DEFAULT_ROUNDS), 3), 8)
    selected_personas = config.get('personas', list(PERSONAS.keys()))
    selected_personas = [p for p in selected_personas if p in PERSONAS]
    if len(selected_personas) < 2:
        selected_personas = list(PERSONAS.keys())

    sim_config = {
        'total_rounds': total_rounds,
        'personas': selected_personas,
        'monitor_id': monitor_id,
        'scenario': scenario,
    }

    task_id = tm.create_task("simulation", metadata=sim_config)

    thread = threading.Thread(
        target=_run_simulation,
        args=(task_id, monitor_id, scenario, sim_config),
        daemon=True,
    )
    thread.start()
    return task_id


def _run_simulation(task_id: str, monitor_id: str, scenario: str, config: Dict):
    """Main simulation loop — runs in background thread."""
    tm = TaskManager()
    total_rounds = config['total_rounds']
    persona_keys = config['personas']

    tm.update_task(
        task_id,
        status=TaskStatus.PROCESSING,
        progress=0,
        message="Initializing simulation...",
        progress_detail={
            "rounds": [],
            "current_round": 0,
            "total_rounds": total_rounds,
            "personas": persona_keys,
            "simulation_id": None,
        },
    )

    try:
        client = ClaudeClient()
        monitor = Monitor.get_by_id(monitor_id)
        brand = monitor.name if monitor else "the brand"
        industry = "technology"  # default; could be derived from monitor keywords

        # Fetch historical context
        historical_stats = {}
        try:
            historical_stats = get_dashboard_stats(monitor_id)
        except Exception:
            pass

        all_rounds = []
        cumulative_actions = []

        for round_num in range(1, total_rounds + 1):
            time_label = TIME_LABELS.get(round_num, f"Round {round_num}")
            progress_pct = int((round_num - 1) / (total_rounds + 1) * 100)

            tm.update_task(
                task_id,
                progress=progress_pct,
                message=f"Round {round_num}/{total_rounds}: {time_label}",
            )

            # Execute round
            round_actions = _execute_round(
                client=client,
                round_num=round_num,
                time_label=time_label,
                total_rounds=total_rounds,
                scenario=scenario,
                brand=brand,
                industry=industry,
                persona_keys=persona_keys,
                previous_rounds=all_rounds,
                cumulative_actions=cumulative_actions,
                historical_stats=historical_stats,
            )

            # Compute metrics
            cumulative_actions.extend(
                a for a in round_actions if a.get('action_type') != 'no_action'
            )
            round_metrics = _compute_round_metrics(
                round_actions, cumulative_actions, persona_keys
            )

            round_data = {
                "round_number": round_num,
                "time_label": time_label,
                "actions": round_actions,
                "metrics": round_metrics,
            }
            all_rounds.append(round_data)

            # Update progress_detail so frontend can poll
            detail = tm.get_task(task_id).progress_detail
            detail = copy.deepcopy(detail) if detail else {}
            detail["rounds"] = copy.deepcopy(all_rounds)
            detail["current_round"] = round_num
            tm.update_task(task_id, progress_detail=detail)

            logger.info(
                f"Simulation {task_id}: Round {round_num}/{total_rounds} complete "
                f"(sentiment={round_metrics.get('avg_sentiment', 0):.2f}, "
                f"crisis={round_metrics.get('crisis_level', 0):.2f})"
            )

        # Generate final summary
        tm.update_task(task_id, progress=90, message="Generating final analysis...")
        aggregate_metrics = _generate_summary(
            client, all_rounds, scenario, brand, persona_keys
        )

        # Persist to DB
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        try:
            Simulation.create(
                simulation_id=simulation_id,
                monitor_id=monitor_id,
                scenario=scenario,
                config=config,
                total_rounds=total_rounds,
                rounds=all_rounds,
                aggregate_metrics=aggregate_metrics,
            )
        except Exception as db_err:
            logger.error(f"Failed to persist simulation: {db_err}")

        # Complete
        result = {
            "simulation_id": simulation_id,
            "total_rounds": total_rounds,
            "rounds": all_rounds,
            "aggregate_metrics": aggregate_metrics,
        }
        detail = tm.get_task(task_id).progress_detail
        detail = copy.deepcopy(detail) if detail else {}
        detail["simulation_id"] = simulation_id
        detail["rounds"] = all_rounds
        detail["aggregate_metrics"] = aggregate_metrics
        tm.update_task(task_id, progress_detail=detail)
        tm.complete_task(task_id, result=result)

        logger.info(f"Simulation {simulation_id} completed successfully")

    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        tm.fail_task(task_id, str(e))


def _execute_round(
    client, round_num, time_label, total_rounds, scenario, brand, industry,
    persona_keys, previous_rounds, cumulative_actions, historical_stats,
) -> List[Dict]:
    """Execute one round: call Claude for each persona sequentially."""
    history_text = _summarize_previous_rounds(previous_rounds)
    current_metrics = _get_current_aggregate(cumulative_actions, persona_keys)

    actions = []
    for persona_key in persona_keys:
        persona = PERSONAS[persona_key]
        try:
            action = _call_persona(
                client=client,
                persona_key=persona_key,
                persona=persona,
                round_num=round_num,
                time_label=time_label,
                total_rounds=total_rounds,
                scenario=scenario,
                brand=brand,
                industry=industry,
                history_text=history_text,
                current_metrics=current_metrics,
                historical_stats=historical_stats,
            )
            action["persona"] = persona_key
            action["platform"] = persona["platform"]
            actions.append(action)
        except Exception as e:
            logger.error(f"Persona {persona_key} failed in round {round_num}: {e}")
            actions.append({
                "persona": persona_key,
                "platform": persona["platform"],
                "action_type": "no_action",
                "title": f"[Error: {persona_key} could not respond]",
                "content": str(e),
                "sentiment_score": 0.0,
                "reach_estimate": 0,
                "reasoning": "Agent error",
            })

    return actions


PERSONA_PROMPT = """You are playing the role of a {persona_name} in a PR crisis simulation.

{system_prompt}

SCENARIO: {scenario}
BRAND: {brand}

CURRENT TIME: {time_label} (Round {round_num} of {total_rounds})

{history_section}

CURRENT AGGREGATE METRICS:
- Overall sentiment: {current_sentiment}
- Total media volume: {current_volume} pieces
- Crisis level: {current_crisis}

{historical_section}

Based on the scenario, the current time period, and what has happened so far, decide your next action.

Choose one action_type from: {action_types}
(Choose "no_action" if it's strategically better to stay silent this round.)

Respond with JSON:
{{
    "action_type": "one of your available types",
    "title": "headline or title of your action (max 100 chars)",
    "content": "2-3 sentence description of what you publish/post/say",
    "sentiment_score": float from -1.0 (very negative toward the brand) to 1.0 (very positive),
    "reach_estimate": integer estimated audience reach,
    "reasoning": "1 sentence explaining why you chose this action now"
}}"""


def _call_persona(
    client, persona_key, persona, round_num, time_label, total_rounds,
    scenario, brand, industry, history_text, current_metrics, historical_stats,
) -> Dict:
    """Call Claude as a specific persona and return structured action."""
    system_prompt = persona["system_prompt"].format(
        brand=brand, industry=industry
    )

    history_section = ""
    if history_text:
        history_section = f"WHAT HAS HAPPENED SO FAR:\n{history_text}"

    historical_section = ""
    if historical_stats:
        historical_section = (
            f"HISTORICAL CONTEXT (real data from last 7 days before simulation):\n"
            f"  Total real mentions: {historical_stats.get('total_mentions', 'N/A')}\n"
            f"  Avg real sentiment: {historical_stats.get('avg_sentiment', 'N/A')}\n"
            f"  Crisis alerts: {historical_stats.get('crisis_count', 'N/A')}"
        )

    prompt = PERSONA_PROMPT.format(
        persona_name=persona["name"],
        system_prompt=system_prompt,
        scenario=scenario,
        brand=brand,
        time_label=time_label,
        round_num=round_num,
        total_rounds=total_rounds,
        history_section=history_section,
        current_sentiment=f"{current_metrics.get('avg_sentiment', 0.0):.2f}",
        current_volume=current_metrics.get('total_volume', 0),
        current_crisis=f"{current_metrics.get('crisis_level', 0.0):.2f}",
        historical_section=historical_section,
        action_types=", ".join(persona["action_types"]),
    )

    result = client.chat_json(
        messages=[{"role": "user", "content": prompt}],
        system="You are a PR simulation agent. Respond only with the requested JSON.",
        temperature=0.7,
        max_tokens=512,
    )

    # Ensure required fields
    result.setdefault("action_type", "no_action")
    result.setdefault("title", "")
    result.setdefault("content", "")
    result.setdefault("sentiment_score", 0.0)
    result.setdefault("reach_estimate", 0)
    result.setdefault("reasoning", "")

    # Clamp sentiment
    result["sentiment_score"] = max(-1.0, min(1.0, float(result["sentiment_score"])))
    # Apply reach multiplier
    result["reach_estimate"] = int(result["reach_estimate"] * persona["reach_multiplier"])

    return result


def _summarize_previous_rounds(previous_rounds: List[Dict]) -> str:
    """Compress previous rounds into a concise text for context."""
    if not previous_rounds:
        return ""

    lines = []
    for rnd in previous_rounds:
        round_label = rnd["time_label"]
        action_lines = []
        for a in rnd["actions"]:
            if a["action_type"] == "no_action":
                action_lines.append(f"  - {a['persona'].title()}: stayed silent")
            else:
                action_lines.append(
                    f"  - {a['persona'].title()} [{a['action_type']}]: "
                    f"\"{a['title']}\" (sentiment: {a['sentiment_score']:.1f}, "
                    f"reach: {a['reach_estimate']:,})"
                )
        metrics = rnd.get("metrics", {})
        lines.append(
            f"{round_label}:\n"
            + "\n".join(action_lines)
            + f"\n  Aggregate: sentiment={metrics.get('avg_sentiment', 0):.2f}, "
            f"crisis={metrics.get('crisis_level', 0):.2f}, "
            f"volume={metrics.get('total_volume', 0)}"
        )

    return "\n\n".join(lines)


def _get_current_aggregate(cumulative_actions: List[Dict], persona_keys: List[str]) -> Dict:
    """Quick aggregate from all actions so far."""
    if not cumulative_actions:
        return {"avg_sentiment": 0.0, "total_volume": 0, "crisis_level": 0.0}

    total_weight = 0.0
    weighted_sentiment = 0.0
    for a in cumulative_actions:
        persona = PERSONAS.get(a.get("persona", ""), {})
        w = persona.get("influence_weight", 0.2)
        weighted_sentiment += a.get("sentiment_score", 0.0) * w
        total_weight += w

    avg_sent = weighted_sentiment / total_weight if total_weight > 0 else 0.0
    volume = len(cumulative_actions)
    crisis = _compute_crisis_level(avg_sent, volume)

    return {"avg_sentiment": avg_sent, "total_volume": volume, "crisis_level": crisis}


def _compute_crisis_level(avg_sentiment: float, volume: int) -> float:
    """Derive crisis level from sentiment and volume."""
    negativity = max(0.0, -avg_sentiment)
    volume_factor = min(volume / 10.0, 2.0)  # caps at 2x
    crisis = negativity * (0.5 + 0.5 * volume_factor)
    return round(min(1.0, crisis), 3)


def _compute_round_metrics(
    round_actions: List[Dict], cumulative_actions: List[Dict], persona_keys: List[str]
) -> Dict:
    """Compute metrics for a single round."""
    agg = _get_current_aggregate(cumulative_actions, persona_keys)

    # Per-persona sentiment for this round
    sentiment_by_persona = {}
    for a in round_actions:
        if a.get("action_type") != "no_action":
            sentiment_by_persona[a["persona"]] = round(a.get("sentiment_score", 0.0), 3)

    # Dominant narrative = highest-reach action
    active = [a for a in round_actions if a.get("action_type") != "no_action"]
    dominant = ""
    if active:
        top = max(active, key=lambda x: x.get("reach_estimate", 0))
        dominant = top.get("title", "")

    return {
        "avg_sentiment": round(agg["avg_sentiment"], 3),
        "total_volume": agg["total_volume"],
        "crisis_level": agg["crisis_level"],
        "round_volume": len(active),
        "sentiment_by_persona": sentiment_by_persona,
        "dominant_narrative": dominant,
    }


SUMMARY_PROMPT = """You are a senior PR strategist analyzing the results of a media simulation.

SCENARIO: {scenario}
BRAND: {brand}

SIMULATION RESULTS ({total_rounds} rounds):
{rounds_text}

Produce a final analysis as JSON:
{{
    "final_sentiment": float (-1.0 to 1.0, where things settled),
    "peak_crisis_level": float (0.0-1.0, the worst it got),
    "total_volume": integer (total media pieces produced),
    "sentiment_trajectory": [float array, one per round],
    "crisis_trajectory": [float array, one per round],
    "key_turning_points": ["Round N: description", ...],
    "recommended_actions": ["action1", "action2", ...],
    "narrative_summary": "3-4 paragraph executive summary of how the scenario played out, key dynamics, and what the brand should do"
}}"""


def _generate_summary(
    client, all_rounds: List[Dict], scenario: str, brand: str, persona_keys: List[str]
) -> Dict:
    """Generate final aggregate metrics via Claude."""
    rounds_text = _summarize_previous_rounds(all_rounds)

    try:
        result = client.chat_json(
            messages=[{
                "role": "user",
                "content": SUMMARY_PROMPT.format(
                    scenario=scenario,
                    brand=brand,
                    total_rounds=len(all_rounds),
                    rounds_text=rounds_text,
                ),
            }],
            system="You are a world-class PR strategist. Provide realistic, actionable analysis.",
            temperature=0.3,
            max_tokens=4096,
        )

        # Ensure fields
        result.setdefault("final_sentiment", 0.0)
        result.setdefault("peak_crisis_level", 0.0)
        result.setdefault("total_volume", 0)
        result.setdefault("sentiment_trajectory", [])
        result.setdefault("crisis_trajectory", [])
        result.setdefault("key_turning_points", [])
        result.setdefault("recommended_actions", [])
        result.setdefault("narrative_summary", "")

        return result

    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        # Fallback: compute from round data
        return {
            "final_sentiment": all_rounds[-1]["metrics"]["avg_sentiment"] if all_rounds else 0,
            "peak_crisis_level": max(r["metrics"]["crisis_level"] for r in all_rounds) if all_rounds else 0,
            "total_volume": sum(r["metrics"]["round_volume"] for r in all_rounds),
            "sentiment_trajectory": [r["metrics"]["avg_sentiment"] for r in all_rounds],
            "crisis_trajectory": [r["metrics"]["crisis_level"] for r in all_rounds],
            "key_turning_points": [],
            "recommended_actions": [],
            "narrative_summary": f"Simulation completed with {len(all_rounds)} rounds. Summary generation failed: {e}",
        }
