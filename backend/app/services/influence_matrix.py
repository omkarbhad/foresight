"""Cross-agent influence graph for CrewAI simulation engine.

Defines which agents influence which others, and provides context
filtering so each agent sees only relevant actions from influencing agents.
"""

from typing import Dict, List

# Execution order — news breaks first, brand responds last
AGENT_ORDER = [
    "journalist", "analyst", "influencer", "consumer",
    "investor", "competitor", "regulator", "brand_pr",
]

# Influence matrix: who influences whom
# Key = agent, Value = list of agents it influences
INFLUENCE_OUTGOING = {
    "journalist":  ["consumer", "analyst", "influencer", "investor"],
    "analyst":     ["investor", "competitor", "brand_pr"],
    "influencer":  ["consumer", "journalist", "brand_pr"],
    "consumer":    ["brand_pr", "influencer", "journalist"],
    "investor":    ["analyst", "brand_pr", "competitor"],
    "competitor":  ["journalist", "consumer"],
    "regulator":   ["journalist", "analyst", "influencer", "consumer", "investor", "competitor", "brand_pr"],
    "brand_pr":    ["consumer", "journalist", "investor"],
}

# Precompute the inverse: who influences a given agent
INFLUENCE_INCOMING: Dict[str, List[str]] = {}
for _source, _targets in INFLUENCE_OUTGOING.items():
    for _target in _targets:
        INFLUENCE_INCOMING.setdefault(_target, []).append(_source)
# regulator is influenced by all others (anyone can trigger regulatory attention)
INFLUENCE_INCOMING.setdefault("regulator", list(
    set(AGENT_ORDER) - {"regulator"}
))


def compute_influence_incoming(influence_outgoing: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Compute the inverse influence map from an outgoing map.

    Given {A: [B, C]} (A influences B and C), returns {B: [A], C: [A]}.
    """
    incoming: Dict[str, List[str]] = {}
    for source, targets in influence_outgoing.items():
        for target in targets:
            incoming.setdefault(target, []).append(source)
    return incoming


def get_influence_context(
    agent_key: str,
    round_actions: List[Dict],
    previous_rounds: List[Dict],
    influence_incoming: Dict[str, List[str]] = None,
    agent_scenario_map: Dict[str, str] = None,
) -> str:
    """Build influence context for a specific agent.

    Includes:
    - Actions from this round by agents that influence the current agent
    - Most recent actions from the previous round by influencing agents
      (for agents that haven't acted yet this round)

    Args:
        influence_incoming: Dynamic influence map. Falls back to static INFLUENCE_INCOMING.
        agent_scenario_map: Optional mapping of agent_key → scenario string for
            cross-scenario context tagging.

    Returns formatted text string.
    """
    incoming = influence_incoming or INFLUENCE_INCOMING
    influencers = incoming.get(agent_key, [])
    if not influencers:
        return ""

    lines = []

    # Current round actions from influencing agents
    current_seen = set()
    for action in round_actions:
        source = action.get("persona", "")
        if source in influencers and action.get("action_type") != "no_action":
            current_seen.add(source)
            scenario_tag = agent_scenario_map.get(source, "") if agent_scenario_map else ""
            lines.append(_format_action(action, tag="This Round", scenario_tag=scenario_tag))

    # Previous round — fill in influencers who haven't acted this round yet
    if previous_rounds:
        last_round = previous_rounds[-1]
        for action in last_round.get("actions", []):
            source = action.get("persona", "")
            if (source in influencers
                    and source not in current_seen
                    and action.get("action_type") != "no_action"):
                scenario_tag = agent_scenario_map.get(source, "") if agent_scenario_map else ""
                lines.append(_format_action(action, tag="Previous Round", scenario_tag=scenario_tag))

    if not lines:
        return ""

    return "INFLUENCE CONTEXT (actions from agents that affect you):\n" + "\n".join(lines)


def _format_action(action: Dict, tag: str, scenario_tag: str = "") -> str:
    """Format a single action for influence context."""
    persona = action.get("persona", "unknown").replace("_", " ").title()
    action_type = action.get("action_type", "action")
    title = action.get("title", "")
    sentiment = action.get("sentiment_score", 0.0)
    reach = action.get("reach_estimate", 0)

    reach_str = _format_reach(reach)
    scenario_info = f" [Scenario: {scenario_tag}]" if scenario_tag else ""
    return (
        f"  [{tag}]{scenario_info} {persona} — {action_type}: \"{title}\" "
        f"(sentiment: {sentiment:.1f}, reach: {reach_str})"
    )


def _format_reach(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def get_agent_order(selected_agents: List[str], custom_order: List[str] = None) -> List[str]:
    """Return selected agents in execution order.

    Args:
        custom_order: Dynamic execution order. Falls back to static AGENT_ORDER.
    """
    order = custom_order or AGENT_ORDER
    return [a for a in order if a in selected_agents]
