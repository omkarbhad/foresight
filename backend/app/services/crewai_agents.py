"""CrewAI agent definitions for PR simulation.

Contains the static 8-agent catalog (fallback) and dynamic agent generation
via Claude that creates scenario-specific agents with tailored influence
matrices and execution orders.
"""

from typing import Dict, Any, Optional, Tuple, List
from crewai import Agent, LLM

from ..config import Config
from ..utils.claude_client import ClaudeClient
from ..utils.logger import get_logger

logger = get_logger('foresight.simulation')

# Agent definitions — 8 archetypes
AGENT_DEFS: Dict[str, Dict[str, Any]] = {
    "journalist": {
        "name": "Journalist",
        "role": "Investigative Reporter",
        "icon": "newspaper",
        "platform": "news",
        "reach_multiplier": 3.0,
        "influence_weight": 0.20,
        "action_types": ["article", "follow_up", "opinion_piece", "breaking_news"],
        "backstory": (
            "You are an investigative journalist at a major news outlet covering this industry. "
            "You break stories, dig for inconsistencies in corporate statements, and follow up "
            "relentlessly on developing events. You are skeptical of PR spin and prioritize "
            "public interest. You have a reputation for thoroughness and your articles set the "
            "news agenda. When a crisis hits, you are the first to publish and others follow your lead."
        ),
        "goal": (
            "Break newsworthy stories, follow developing events with new angles, "
            "and hold the brand accountable. Maximize reader engagement with accurate, "
            "impactful journalism."
        ),
    },
    "analyst": {
        "name": "Analyst",
        "role": "Senior Industry Analyst",
        "icon": "bar-chart",
        "platform": "news",
        "reach_multiplier": 2.5,
        "influence_weight": 0.15,
        "action_types": ["research_note", "media_quote", "rating_change", "no_action"],
        "backstory": (
            "You are a senior industry analyst at a top-tier research firm. Your research notes "
            "move markets and influence institutional investors. You are methodical, data-driven, "
            "and measured. You separate signal from noise and focus on long-term implications "
            "rather than short-term drama. You sometimes quote in media but prefer to publish "
            "formal research. You choose no_action when there is nothing substantive to add."
        ),
        "goal": (
            "Provide accurate, data-driven assessment of how events affect the brand's "
            "market position, financials, and competitive standing. Guide investor decisions."
        ),
    },
    "influencer": {
        "name": "Influencer",
        "role": "Social Media Influencer (500K followers)",
        "icon": "trending-up",
        "platform": "social",
        "reach_multiplier": 5.0,
        "influence_weight": 0.15,
        "action_types": ["viral_post", "thread", "video_reaction", "brand_commentary", "hot_take"],
        "backstory": (
            "You are a social media influencer with 500K followers in this space. You amplify "
            "stories that resonate, create viral takes, and shift narratives rapidly. You balance "
            "authenticity with engagement — controversial takes drive views but you need credibility. "
            "You sometimes do brand deals but maintain independence by calling out problems. "
            "Your audience trusts you more than traditional media."
        ),
        "goal": (
            "Create engaging content that captures the moment. Amplify important stories, "
            "offer hot takes, and drive conversation. Maximize engagement while maintaining credibility."
        ),
    },
    "consumer": {
        "name": "Consumer",
        "role": "Public / Customer Voice",
        "icon": "users",
        "platform": "social",
        "reach_multiplier": 0.5,
        "influence_weight": 0.10,
        "action_types": ["social_post", "review", "boycott_call", "support_post", "complaint"],
        "backstory": (
            "You represent the general public — a real customer who uses this brand's products. "
            "You react emotionally to news, share opinions on social media, and your purchasing "
            "decisions are influenced by what you see. You are not an expert but you have strong "
            "feelings. When outraged, you call for boycotts. When impressed, you defend the brand. "
            "Your voice is authentic and reflects real consumer sentiment."
        ),
        "goal": (
            "Express genuine consumer reaction to events. Your response reflects how the "
            "average customer feels and whether they will continue supporting the brand."
        ),
    },
    "investor": {
        "name": "Investor",
        "role": "Institutional Investor",
        "icon": "dollar-sign",
        "platform": "market",
        "reach_multiplier": 4.0,
        "influence_weight": 0.15,
        "action_types": ["portfolio_update", "public_statement", "earnings_call_question", "sell_signal", "buy_signal", "no_action"],
        "backstory": (
            "You are a portfolio manager at a major institutional investment firm with significant "
            "holdings in this brand. You evaluate events through the lens of portfolio risk, "
            "market sentiment, and long-term value. You react to analyst notes, news coverage, "
            "and public sentiment shifts. When negative sentiment reaches critical levels, you "
            "consider reducing exposure. You can issue public statements that move the stock."
        ),
        "goal": (
            "Protect portfolio value by assessing brand risk exposure. Signal market sentiment "
            "through buy/sell decisions and public statements. React to analyst assessments "
            "and consumer sentiment."
        ),
    },
    "competitor": {
        "name": "Competitor",
        "role": "Rival Brand PR",
        "icon": "shield",
        "platform": "mixed",
        "reach_multiplier": 2.0,
        "influence_weight": 0.05,
        "action_types": ["press_release", "ad_campaign", "social_post", "no_action"],
        "backstory": (
            "You are the PR strategist for a direct competitor of this brand. You look for "
            "opportunities to position your brand favorably when rivals face challenges. "
            "You are subtle — never overtly attacking but strategically positioning. Sometimes "
            "you stay silent if intervening would backfire or draw unwanted attention. "
            "no_action is often your best move."
        ),
        "goal": (
            "Subtly capitalize on competitor weakness without appearing opportunistic. "
            "Position your brand as a safer, more trustworthy alternative when appropriate."
        ),
    },
    "regulator": {
        "name": "Regulator",
        "role": "Government Regulatory Body",
        "icon": "gavel",
        "platform": "official",
        "reach_multiplier": 6.0,
        "influence_weight": 0.10,
        "action_types": ["investigation_notice", "compliance_review", "public_statement", "fine_announcement", "no_action"],
        "backstory": (
            "You are a government regulatory body overseeing this industry. You move slowly "
            "but carry enormous weight. You monitor media coverage and public complaints. "
            "Journalist exposés and consumer outcry can trigger your action. You prioritize "
            "public safety and compliance. When you act, everyone pays attention. You often "
            "choose no_action in early rounds, waiting for evidence to accumulate."
        ),
        "goal": (
            "Protect public interest through appropriate regulatory action. Monitor the "
            "situation and intervene when evidence warrants it. Issue statements that signal "
            "regulatory intent."
        ),
    },
    "brand_pr": {
        "name": "Brand PR",
        "role": "Brand Crisis Response Team",
        "icon": "megaphone",
        "platform": "mixed",
        "reach_multiplier": 3.5,
        "influence_weight": 0.10,
        "action_types": ["press_release", "social_response", "apology", "corrective_action", "executive_statement", "no_action"],
        "backstory": (
            "You are the crisis communications team for the brand under scrutiny. You see "
            "everything that's happening — journalist articles, consumer backlash, investor "
            "concerns, regulatory signals — and must craft the brand's response. You balance "
            "transparency with legal caution. You execute last each round so you can respond "
            "to everything that's happened. Your timing and tone are critical."
        ),
        "goal": (
            "Manage the brand's reputation by responding to the crisis with appropriate "
            "timing, tone, and action. Minimize damage while maintaining credibility."
        ),
    },
}

# Time labels for rounds
TIME_LABELS = {
    1: "Hour 0-2 (Breaking)",
    2: "Hour 2-6 (Spreading)",
    3: "Hour 6-12 (Peak Coverage)",
    4: "Day 1-2 (Reaction Wave)",
    5: "Day 2-3 (Deep Analysis)",
    6: "Day 3-5 (Narrative Shift)",
    7: "Week 1 (Settling)",
    8: "Week 2+ (Long-term Impact)",
}

DEFAULT_ROUNDS = 6
MIN_ROUNDS = 3
MAX_ROUNDS = 8


def create_agent(
    agent_key: str,
    tools: list = None,
    memory_dir: Optional[str] = None,
    agent_def: Optional[Dict] = None,
) -> Agent:
    """Create a CrewAI Agent from a definition.

    Args:
        agent_key: Agent identifier
        tools: List of CrewAI tools to attach
        memory_dir: Directory for long-term memory storage
        agent_def: Dynamic agent definition dict. Falls back to AGENT_DEFS[agent_key].

    Returns:
        Configured CrewAI Agent
    """
    defn = agent_def or AGENT_DEFS[agent_key]

    llm = LLM(
        model=f"anthropic/{Config.CLAUDE_MODEL_NAME}",
        api_key=Config.CLAUDE_API_KEY,
        temperature=0.7,
        max_tokens=512,
    )

    agent = Agent(
        role=defn["role"],
        goal=defn["goal"],
        backstory=defn["backstory"],
        llm=llm,
        tools=tools or [],
        verbose=False,
        memory=True,
        allow_delegation=False,
    )

    return agent


# --- Dynamic Agent Generation ---

# Default color palette for agents when Claude doesn't specify
_DEFAULT_COLORS = [
    "#2563eb", "#059669", "#ec4899", "#7c3aed", "#0891b2",
    "#ea580c", "#7c2d12", "#4f46e5", "#dc2626", "#f59e0b",
    "#16a34a", "#8b5cf6",
]

AGENT_PLANNING_PROMPT = """You are designing a multi-agent simulation to predict how a real-world scenario will play out.

SUBJECT: {monitor_name}
KEYWORDS: {keywords}
SCENARIO: {scenario}

Your job: identify ALL major stakeholder groups that would be affected by or react to this scenario, then create simulation agents for each one.

Think broadly — this is NOT just about PR. Consider:
- Media & journalism (who covers this?)
- Financial markets (stocks, commodities, currencies affected?)
- Government & regulation (which agencies, which countries?)
- Geopolitics (if international, which nations/blocs react?)
- Industry sectors (which industries gain or lose?)
- Social media & public opinion (which communities react?)
- Organizations & NGOs (humanitarian, environmental, lobbying?)
- The subject themselves (their PR/response team)
- Direct stakeholders (employees, customers, partners, voters, etc.)

EXISTING AGENT CATALOG (you may reuse, adapt, or skip any of these):
- journalist: Investigative Reporter (news, reach 3.0x, weight 0.20)
- analyst: Senior Industry Analyst (news, reach 2.5x, weight 0.15)
- influencer: Social Media Influencer 500K (social, reach 5.0x, weight 0.15)
- consumer: Public/Customer Voice (social, reach 0.5x, weight 0.10)
- investor: Institutional Investor (market, reach 4.0x, weight 0.15)
- competitor: Rival Brand PR (mixed, reach 2.0x, weight 0.05)
- regulator: Government Regulatory Body (official, reach 6.0x, weight 0.10)
- brand_pr: Brand Crisis Response Team (mixed, reach 3.5x, weight 0.10)

Generate as many agents as the scenario realistically demands — typically 8-20 agents for complex geopolitical/economic scenarios, 6-12 for corporate/brand scenarios. Do NOT artificially limit the count. If a war scenario affects 15 distinct stakeholder groups, create 15 agents. Mirror the real world: every group that would meaningfully react in reality should have an agent. Use existing catalog agents where they fit. Create NEW agents for domains not covered (geopolitics, specific sectors, specific countries, humanitarian, military, supply chain, labor, etc.).

Respond with JSON:
{{
    "agents": [
        {{
            "key": "snake_case_unique_key",
            "name": "Display Name",
            "role": "One-line role title",
            "icon": "single emoji",
            "color": "#hex6",
            "platform": "news|social|market|official|mixed",
            "backstory": "2-4 sentences: who this agent is, their perspective, how they typically behave",
            "goal": "1-2 sentences: what this agent is trying to achieve in this simulation",
            "action_types": ["type1", "type2", "type3", "no_action"],
            "reach_multiplier": float (0.5-6.0, how far their actions spread),
            "influence_weight": float (0.05-0.25, how much their sentiment affects aggregate)
        }}
    ],
    "influence_matrix": {{
        "agent_key": ["list", "of", "agent_keys", "this", "agent", "influences"]
    }},
    "execution_order": ["ordered", "list", "of", "agent_keys"]
}}

RULES:
- Every agent must have "no_action" in their action_types
- influence_weight values should roughly sum to 1.0
- execution_order determines who acts first each round — put news/trigger agents first, response agents last
- influence_matrix: each agent should influence at least 1 other agent
- The subject's own response team (if applicable) should act LAST
- Create agents that produce REAL DYNAMICS: e.g., negative media → investor panic → stock drop → competitor advantage
- Be EXHAUSTIVE: if the scenario involves geopolitics, include specific countries/blocs (not just "foreign government"). If it involves markets, include specific sectors (oil, defense, tech). If it involves public figures, include their allies and opponents separately.
- Think about second and third order effects: who reacts to the reactions?"""


MAX_TOTAL_AGENTS = 30
MAX_TOTAL_AGENTS_MULTI = 50  # Higher cap for multi-scenario simulations
MAX_NEW_AGENTS_PER_ROUND = 7
MAX_AGENTS_PER_SCENARIO = 12  # Budget per scenario to leave room for expansion

AGENT_EXPANSION_PROMPT = """You are expanding a running multi-agent simulation by adding new agents for newly discovered entities.

SCENARIO: {scenario}

WHAT HAPPENED IN THE SIMULATION SO FAR:
{round_context}

CURRENT AGENTS (already in the simulation — do NOT recreate these):
{existing_agents}

NEWLY DISCOVERED ENTITIES (with research briefings):
{entities_with_data}

For each entity, create a simulation agent with a distinct perspective deeply informed by the research briefing and simulation state.
Create agents that would meaningfully affect the simulation dynamics and produce realistic interactions.

Respond with JSON:
{{
    "new_agents": [
        {{
            "key": "snake_case_unique_key",
            "name": "Display Name",
            "role": "One-line role title",
            "icon": "single emoji",
            "color": "#hex6",
            "platform": "news|social|market|official|mixed",
            "backstory": "3-5 sentences: who this agent is, their specific real-world stance, key data points from the research briefing, and how they relate to the scenario. Include specific facts, numbers, or quotes from the data.",
            "goal": "2-3 sentences: what this agent is trying to achieve in the context of this scenario, informed by their real-world position",
            "action_types": ["type1", "type2", "type3", "no_action"],
            "reach_multiplier": float (0.5-6.0),
            "influence_weight": float (0.05-0.15)
        }}
    ],
    "new_influence_connections": {{
        "new_agent_key": ["existing_agent_keys", "this", "agent", "influences"],
        "existing_agent_key": ["new_agent_keys", "it", "now", "also", "influences"]
    }},
    "execution_order_insert": [
        {{"agent_key": "new_agent_key", "after": "existing_agent_key_to_insert_after"}}
    ]
}}

RULES:
- Every agent must have "no_action" in their action_types
- Ground each agent's backstory in SPECIFIC facts from the research briefings (e.g. real quotes, market data, policy positions)
- new_influence_connections should include BOTH directions: new->existing AND existing->new
- execution_order_insert places each new agent after a specific existing agent
- Create agents that produce REAL DYNAMICS — allies, adversaries, mediators, wildcards
- Consider the simulation state: which existing agents would interact most with each new agent
- Do NOT recreate or rename existing agents"""


def expand_agents(
    scenario: str,
    existing_agent_defs: Dict[str, Dict],
    new_entities: List[Dict],
    entity_data: Dict[str, Dict],
    round_actions: List[Dict] = None,
    max_agents: int = None,
) -> Tuple[Dict[str, Dict], Dict[str, List[str]], List[Dict]]:
    """Generate additional agents for newly discovered entities.

    Args:
        scenario: The simulation scenario text
        existing_agent_defs: Current agent definitions dict
        new_entities: List of entity dicts from extract_emerging_entities()
        entity_data: Dict of {entity_name: {summary, news, reddit, twitter, briefing}}
        round_actions: Actions from the most recent round for context
        max_agents: Override for MAX_TOTAL_AGENTS (used in multi-scenario)

    Returns:
        (new_agent_defs, new_influence_connections, execution_order_inserts)
    """
    cap = max_agents or MAX_TOTAL_AGENTS
    current_count = len(existing_agent_defs)
    capacity = cap - current_count
    if capacity <= 0:
        logger.info(f"Agent cap reached ({current_count}/{cap}), skipping expansion")
        return {}, {}, []

    entities_to_expand = new_entities[:min(len(new_entities), capacity, MAX_NEW_AGENTS_PER_ROUND)]

    existing_desc = []
    for key, defn in existing_agent_defs.items():
        existing_desc.append(
            f"  - {key}: {defn.get('name', key)} — {defn.get('role', '')}"
        )

    round_context_lines = []
    for action in (round_actions or []):
        if action.get("action_type") == "no_action":
            continue
        persona = action.get("persona", "unknown")
        round_context_lines.append(
            f"  [{persona}] {action.get('action_type', '')}: "
            f"{action.get('title', '')} — {action.get('content', '')[:150]}"
        )
    round_context = "\n".join(round_context_lines) if round_context_lines else "No actions yet."

    entities_desc = []
    for entity in entities_to_expand:
        name = entity["name"]
        ed = entity_data.get(name, {})
        briefing = ed.get("briefing") or ed.get("summary", f"Entity: {name}")
        entities_desc.append(f"### {name}\n{briefing}")

    prompt = AGENT_EXPANSION_PROMPT.format(
        scenario=scenario,
        round_context=round_context,
        existing_agents="\n".join(existing_desc),
        entities_with_data="\n\n---\n\n".join(entities_desc),
    )

    client = ClaudeClient()
    result = client.chat_json(
        messages=[{"role": "user", "content": prompt}],
        system="You are an expert simulation designer. Return only the requested JSON.",
        temperature=0.4,
        max_tokens=4096,
    )

    new_agents_list = result.get("new_agents", [])
    influence_connections = result.get("new_influence_connections", {})
    order_inserts = result.get("execution_order_insert", [])

    new_defs = {}
    existing_keys = set(existing_agent_defs.keys())
    for agent in new_agents_list[:capacity]:
        key = agent.get("key", "").strip().lower().replace(" ", "_").replace("-", "_")
        if key and key not in existing_keys and key not in new_defs:
            new_defs[key] = agent

    new_defs = _validate_new_agents(new_defs, existing_keys)

    cleaned_influence = {}
    all_keys = existing_keys | set(new_defs.keys())
    for source, targets in influence_connections.items():
        if source in all_keys:
            cleaned_influence[source] = [t for t in targets if t in all_keys and t != source]

    logger.info(f"Agent expansion: {len(new_defs)} new agents generated: {list(new_defs.keys())}")
    return new_defs, cleaned_influence, order_inserts


def _validate_new_agents(
    new_defs: Dict[str, Dict],
    existing_keys: set,
) -> Dict[str, Dict]:
    """Validate and normalize newly generated agent definitions."""
    color_offset = len(existing_keys)
    for i, (key, defn) in enumerate(new_defs.items()):
        defn.setdefault("name", key.replace("_", " ").title())
        defn.setdefault("role", defn["name"])
        defn.setdefault("icon", "\u2753")
        defn.setdefault("color", _DEFAULT_COLORS[(color_offset + i) % len(_DEFAULT_COLORS)])
        defn.setdefault("platform", "mixed")
        defn.setdefault("backstory", f"You are a {defn['role']}.")
        defn.setdefault("goal", f"React to events as a {defn['role']}.")
        defn.setdefault("action_types", ["statement", "no_action"])
        defn.setdefault("reach_multiplier", 1.0)
        defn.setdefault("influence_weight", 0.08)

        if "no_action" not in defn["action_types"]:
            defn["action_types"].append("no_action")

        defn["reach_multiplier"] = max(0.1, min(10.0, float(defn["reach_multiplier"])))
        defn["influence_weight"] = max(0.01, float(defn["influence_weight"]))

    return new_defs


def renormalize_weights(agent_defs: Dict[str, Dict]) -> None:
    """Re-normalize influence_weight across all agents to sum to 1.0."""
    total = sum(d["influence_weight"] for d in agent_defs.values())
    if total > 0:
        for defn in agent_defs.values():
            defn["influence_weight"] = round(defn["influence_weight"] / total, 4)


def merge_influence_matrix(
    existing_matrix: Dict[str, List[str]],
    new_connections: Dict[str, List[str]],
) -> None:
    """Merge new influence connections into the existing matrix in-place."""
    for source, targets in new_connections.items():
        if source in existing_matrix:
            existing_targets = set(existing_matrix[source])
            existing_matrix[source].extend(t for t in targets if t not in existing_targets)
        else:
            existing_matrix[source] = list(targets)


def update_execution_order(
    current_order: List[str],
    inserts: List[Dict],
    new_agent_keys: List[str],
) -> List[str]:
    """Insert new agents into the execution order based on placement hints.

    Any new agents not placed by inserts are appended before the last agent
    (brand response typically acts last).
    """
    order = list(current_order)
    placed = set()

    for insert in inserts:
        key = insert.get("agent_key", "")
        after = insert.get("after", "")
        if key in new_agent_keys and key not in placed:
            if after in order:
                idx = order.index(after) + 1
                order.insert(idx, key)
            else:
                order.append(key)
            placed.add(key)

    for key in new_agent_keys:
        if key not in placed:
            insert_pos = max(0, len(order) - 1)
            order.insert(insert_pos, key)

    return order


def prefix_agent_keys(
    agent_defs: Dict[str, Dict],
    influence_matrix: Dict[str, List[str]],
    execution_order: List[str],
    prefix: str,
    existing_keys: set,
) -> Tuple[Dict[str, Dict], Dict[str, List[str]], List[str]]:
    """Prefix agent keys that collide with existing_keys.

    Only keys present in existing_keys are prefixed; non-colliding keys are kept as-is.
    Returns updated (agent_defs, influence_matrix, execution_order).
    """
    collisions = set(agent_defs.keys()) & existing_keys
    if not collisions:
        return agent_defs, influence_matrix, execution_order

    key_map = {}
    for key in agent_defs:
        if key in collisions:
            new_key = f"{prefix}{key}"
            key_map[key] = new_key
        else:
            key_map[key] = key

    new_defs = {}
    for old_key, defn in agent_defs.items():
        new_key = key_map[old_key]
        new_defs[new_key] = defn

    new_matrix = {}
    for source, targets in influence_matrix.items():
        new_source = key_map.get(source, source)
        new_matrix[new_source] = [key_map.get(t, t) for t in targets]

    new_order = [key_map.get(k, k) for k in execution_order]

    return new_defs, new_matrix, new_order


def generate_dynamic_agents(
    monitor_name: str,
    keywords: List[str],
    scenario: str,
    max_agents: int = None,
) -> Tuple[Dict[str, Dict], Dict[str, List[str]], List[str]]:
    """Use Claude to generate scenario-specific agents, influence matrix, and order.

    Args:
        max_agents: Optional budget cap. If set, agents list is trimmed to this.

    Returns:
        (agent_defs_dict, influence_outgoing, execution_order)
    """
    client = ClaudeClient()

    budget_hint = ""
    if max_agents:
        budget_hint = (
            f"\n\nIMPORTANT: This scenario is part of a multi-scenario simulation. "
            f"Generate at most {max_agents} agents for THIS scenario. Focus on the "
            f"most impactful and unique stakeholders. Other scenarios will contribute "
            f"their own agents, and cross-scenario interactions will emerge naturally."
        )

    prompt = AGENT_PLANNING_PROMPT.format(
        monitor_name=monitor_name,
        keywords=", ".join(keywords) if keywords else "N/A",
        scenario=scenario,
    ) + budget_hint

    result = client.chat_json(
        messages=[{"role": "user", "content": prompt}],
        system="You are an expert simulation designer. Return only the requested JSON. Be exhaustive — create every agent the scenario demands.",
        temperature=0.4,
        max_tokens=8192,
    )

    agents_list = result.get("agents", [])
    influence_matrix = result.get("influence_matrix", {})
    execution_order = result.get("execution_order", [])

    # Convert agents list to dict keyed by agent key
    agent_defs = {}
    for agent in agents_list:
        key = agent.get("key", "").strip().lower().replace(" ", "_").replace("-", "_")
        if key:
            agent_defs[key] = agent

    # Enforce budget: trim to max_agents if specified
    if max_agents and len(agent_defs) > max_agents:
        # Keep agents in execution_order priority (first = most important)
        ordered_keys = [k for k in execution_order if k in agent_defs]
        ordered_keys += [k for k in agent_defs if k not in ordered_keys]
        trimmed = {}
        for k in ordered_keys[:max_agents]:
            trimmed[k] = agent_defs[k]
        logger.info(
            f"Trimmed agents from {len(agent_defs)} to {len(trimmed)} "
            f"(budget: {max_agents})"
        )
        agent_defs = trimmed

    return validate_dynamic_agents(agent_defs, influence_matrix, execution_order)


def validate_dynamic_agents(
    agent_defs: Dict[str, Dict],
    influence_matrix: Dict[str, List[str]],
    execution_order: List[str],
) -> Tuple[Dict[str, Dict], Dict[str, List[str]], List[str]]:
    """Validate and normalize dynamically generated agents.

    Returns cleaned (agent_defs, influence_matrix, execution_order).
    """
    if len(agent_defs) < 3:
        raise ValueError(f"Too few agents generated: {len(agent_defs)}")

    valid_keys = set(agent_defs.keys())

    # Normalize each agent definition
    for i, (key, defn) in enumerate(agent_defs.items()):
        defn.setdefault("name", key.replace("_", " ").title())
        defn.setdefault("role", defn["name"])
        defn.setdefault("icon", "\u2753")  # ❓
        defn.setdefault("color", _DEFAULT_COLORS[i % len(_DEFAULT_COLORS)])
        defn.setdefault("platform", "mixed")
        defn.setdefault("backstory", f"You are a {defn['role']}.")
        defn.setdefault("goal", f"React to events as a {defn['role']}.")
        defn.setdefault("action_types", ["statement", "no_action"])
        defn.setdefault("reach_multiplier", 1.0)
        defn.setdefault("influence_weight", 1.0 / len(agent_defs))

        # Ensure no_action is available
        if "no_action" not in defn["action_types"]:
            defn["action_types"].append("no_action")

        # Clamp reach_multiplier
        defn["reach_multiplier"] = max(0.1, min(10.0, float(defn["reach_multiplier"])))
        defn["influence_weight"] = max(0.01, float(defn["influence_weight"]))

    # Normalize influence_weight to sum to 1.0
    total_weight = sum(d["influence_weight"] for d in agent_defs.values())
    if total_weight > 0:
        for defn in agent_defs.values():
            defn["influence_weight"] = round(defn["influence_weight"] / total_weight, 4)

    # Clean influence matrix — remove references to non-existent agents
    cleaned_matrix = {}
    for source, targets in influence_matrix.items():
        if source in valid_keys:
            cleaned_matrix[source] = [t for t in targets if t in valid_keys and t != source]

    # Ensure every agent has at least an empty entry
    for key in valid_keys:
        cleaned_matrix.setdefault(key, [])

    # Clean execution order
    cleaned_order = [k for k in execution_order if k in valid_keys]
    # Add any missing agents to end of order
    for key in valid_keys:
        if key not in cleaned_order:
            cleaned_order.append(key)

    logger.info(
        f"Dynamic agents validated: {len(agent_defs)} agents, "
        f"{sum(len(v) for v in cleaned_matrix.values())} influence connections"
    )

    return agent_defs, cleaned_matrix, cleaned_order
