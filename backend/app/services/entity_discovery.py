"""Entity discovery between simulation rounds.

Analyzes agent outputs to find newly mentioned entities (countries,
organizations, people, etc.) that don't yet have their own agent,
then fetches real-world data about them from News/Reddit/Twitter/Finnhub
to provide context for generating new agent personas.
"""

import re
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.llm_client import get_llm_client
from ..utils.logger import get_logger
from .ingestion import NewsAPIService, RedditService, TwitterService, FinnhubService

logger = get_logger('foresight.entity_discovery')

MAX_ENTITIES_PER_ROUND = 5
MAX_FETCH_PER_ENTITY = 15

ENTITY_EXTRACTION_PROMPT = """Analyze these simulation round outputs and identify NEW actors/entities
that were mentioned or implicated but do NOT already have their own agent.

Focus on entities that would realistically react to or be affected by the scenario
and whose inclusion would meaningfully change the simulation dynamics.

SCENARIO: {scenario}

EXISTING AGENTS (these entities are already represented — do NOT include them):
{existing_agents}

ROUND {round_num} OUTPUTS:
{round_outputs}

Return JSON with entities worth adding as new agents. Only include entities that:
1. Were explicitly mentioned or strongly implied in the round outputs
2. Would have a distinct perspective not covered by existing agents
3. Are specific (e.g. "Russia's Foreign Ministry" not just "foreign governments")

{{
    "new_entities": [
        {{
            "name": "Display Name",
            "type": "country|organization|person|industry|group|military|ngo",
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "relevance": "One sentence on why this entity matters to the scenario"
        }}
    ]
}}

If no meaningful new entities are found, return {{"new_entities": []}}."""


SYNTHESIS_PROMPT = """You are a senior research analyst producing a briefing about the entity "{entity_name}" in the context of this scenario: {scenario}

Here is the raw data collected from multiple sources:

{raw_data}

Produce a ~200-word research briefing that:
1. Summarizes this entity's current real-world position and stance related to the scenario
2. Highlights key actions, statements, or developments from the data
3. Notes any financial/market implications if market data is available
4. Identifies this entity's likely motivations and interests

Write the briefing as a dense, factual paragraph. Include specific data points (quotes, numbers, dates) where available."""


def extract_emerging_entities(
    scenario: str,
    existing_agent_keys: List[str],
    existing_agent_defs: Dict[str, Dict],
    round_actions: List[Dict],
    round_num: int,
) -> List[Dict]:
    """Analyze round outputs to discover new entities not yet represented by agents."""
    agent_descriptions = []
    for key in existing_agent_keys:
        defn = existing_agent_defs.get(key, {})
        name = defn.get("name", key.replace("_", " ").title())
        role = defn.get("role", "")
        agent_descriptions.append(f"  - {key}: {name} ({role})")

    outputs = []
    for action in round_actions:
        if action.get("action_type") == "no_action":
            continue
        persona = action.get("persona", "unknown")
        outputs.append(
            f"[{persona}] ({action.get('action_type', 'unknown')}): "
            f"{action.get('title', '')}\n"
            f"  {action.get('content', '')}"
        )

    if not outputs:
        return []

    prompt = ENTITY_EXTRACTION_PROMPT.format(
        scenario=scenario,
        existing_agents="\n".join(agent_descriptions),
        round_num=round_num,
        round_outputs="\n\n".join(outputs),
    )

    try:
        client = get_llm_client()
        result = client.chat_json(
            messages=[{"role": "user", "content": prompt}],
            system="You are an expert geopolitical and media analyst. Return only the requested JSON.",
            temperature=0.3,
            max_tokens=2048,
        )
        entities = result.get("new_entities", [])

        valid = []
        for e in entities[:MAX_ENTITIES_PER_ROUND]:
            if e.get("name") and e.get("keywords"):
                valid.append({
                    "name": e["name"],
                    "type": e.get("type", "organization"),
                    "keywords": e["keywords"][:5],
                    "relevance": e.get("relevance", ""),
                })

        logger.info(f"Round {round_num}: extracted {len(valid)} emerging entities: "
                     f"{[e['name'] for e in valid]}")
        return valid

    except Exception as e:
        logger.warning(f"Entity extraction failed for round {round_num}: {e}")
        return []


def _extract_scenario_keywords(scenario: str) -> List[str]:
    """Pull 2-3 core keywords from the scenario for query augmentation."""
    stop = {"the", "a", "an", "is", "was", "are", "were", "in", "on", "at",
            "to", "for", "of", "and", "or", "that", "this", "with", "by",
            "from", "has", "had", "be", "been", "will", "would", "could",
            "should", "about", "into", "its", "their", "they", "it", "as"}
    words = re.findall(r"[A-Za-z']+", scenario)
    meaningful = [w for w in words if w.lower() not in stop and len(w) > 2]
    return meaningful[:3]


def fetch_entity_data(
    entities: List[Dict],
    scenario: str,
) -> Dict[str, Dict]:
    """Fetch real-world data for each entity from News/Reddit/Twitter/Finnhub.

    Uses scenario-aware queries, includes article content, and runs a
    Claude synthesis step to produce a research briefing per entity.
    """
    scenario_kws = _extract_scenario_keywords(scenario)
    results = {}

    for entity in entities:
        name = entity["name"]
        keywords = entity["keywords"]
        augmented_keywords = keywords + [kw for kw in scenario_kws if kw.lower() not in
                                         {k.lower() for k in keywords}]

        entity_data = {
            "news": [], "reddit": [], "twitter": [], "finnhub": [],
            "quote": None, "summary": "", "briefing": "",
        }

        fetchers = {
            "news": lambda kws=augmented_keywords: _fetch_news(kws),
            "reddit": lambda kws=augmented_keywords: _fetch_reddit(kws),
            "twitter": lambda kws=augmented_keywords: _fetch_twitter(kws),
            "finnhub": lambda kws=keywords, n=name: _fetch_finnhub(kws, n),
        }

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(fn): source
                for source, fn in fetchers.items()
            }
            for future in as_completed(futures):
                source = futures[future]
                try:
                    result = future.result()
                    if source == "finnhub" and isinstance(result, dict):
                        entity_data["finnhub"] = result.get("articles", [])
                        entity_data["quote"] = result.get("quote")
                    else:
                        entity_data[source] = result
                except Exception as e:
                    logger.warning(f"Fetch {source} failed for '{name}': {e}")

        total = sum(len(entity_data[s]) for s in ("news", "reddit", "twitter", "finnhub"))
        entity_data["summary"] = _build_entity_summary(entity, entity_data)

        try:
            entity_data["briefing"] = _synthesize_briefing(
                entity_name=name,
                scenario=scenario,
                raw_summary=entity_data["summary"],
            )
        except Exception as e:
            logger.warning(f"Synthesis failed for '{name}', using raw summary: {e}")
            entity_data["briefing"] = entity_data["summary"]

        results[name] = entity_data
        logger.info(f"Fetched {total} items for entity '{name}' (briefing: {len(entity_data['briefing'])} chars)")

    return results


def _fetch_news(keywords: List[str]) -> List[Dict]:
    try:
        svc = NewsAPIService()
        mentions = svc.fetch_mentions(keywords=keywords)
        return [
            {
                "title": m.get("title", ""),
                "content": (m.get("content") or "")[:300],
            }
            for m in mentions[:MAX_FETCH_PER_ENTITY]
        ]
    except Exception as e:
        logger.warning(f"[EntityDiscovery] NewsAPI fetch failed: {e}")
        return []


def _fetch_reddit(keywords: List[str]) -> List[Dict]:
    try:
        svc = RedditService()
        mentions = svc.fetch_mentions(keywords=keywords)
        return [
            {
                "title": m.get("title", ""),
                "content": (m.get("content") or "")[:500],
            }
            for m in mentions[:MAX_FETCH_PER_ENTITY]
        ]
    except Exception as e:
        logger.warning(f"[EntityDiscovery] Reddit fetch failed: {e}")
        return []


def _fetch_twitter(keywords: List[str]) -> List[Dict]:
    try:
        svc = TwitterService()
        mentions = svc.fetch_mentions(keywords=keywords)
        return [
            {"content": (m.get("content") or "")[:280]}
            for m in mentions[:MAX_FETCH_PER_ENTITY]
        ]
    except Exception as e:
        logger.warning(f"[EntityDiscovery] Twitter fetch failed: {e}")
        return []


def _fetch_finnhub(keywords: List[str], entity_name: str) -> Dict:
    """Fetch Finnhub company news + quote for an entity."""
    try:
        svc = FinnhubService()
        articles = svc.fetch_mentions(keywords=keywords)
        articles_data = [
            {
                "title": a.get("title", ""),
                "content": (a.get("content") or "")[:300],
                "source": a.get("author", ""),
            }
            for a in articles[:MAX_FETCH_PER_ENTITY]
        ]

        quote = None
        symbols = svc.search_symbol(entity_name)
        if symbols:
            quote = svc.fetch_quote(symbols[0].get("symbol", ""))

        return {"articles": articles_data, "quote": quote}
    except Exception as e:
        logger.warning(f"[EntityDiscovery] Finnhub fetch failed: {e}")
        return {"articles": [], "quote": None}


def _build_entity_summary(entity: Dict, data: Dict) -> str:
    """Build a detailed text summary of fetched data for an entity."""
    parts = [f"Entity: {entity['name']} ({entity['type']})"]
    parts.append(f"Relevance: {entity.get('relevance', 'N/A')}")

    news = data.get("news", [])
    if news:
        parts.append(f"\nNews coverage ({len(news)} articles):")
        for a in news[:6]:
            title = a.get("title", "")
            content = a.get("content", "")
            line = f"  - {title}"
            if content:
                line += f"\n    {content[:200]}"
            parts.append(line)

    reddit = data.get("reddit", [])
    if reddit:
        parts.append(f"\nReddit discussions ({len(reddit)} posts):")
        for p in reddit[:5]:
            title = p.get("title", "")
            content = p.get("content", "")
            line = f"  - {title}"
            if content:
                line += f"\n    {content[:200]}"
            parts.append(line)

    twitter = data.get("twitter", [])
    if twitter:
        parts.append(f"\nTwitter/X chatter ({len(twitter)} tweets):")
        for t in twitter[:4]:
            parts.append(f"  - {t.get('content', '')[:200]}")

    finnhub = data.get("finnhub", [])
    if finnhub:
        parts.append(f"\nFinancial news ({len(finnhub)} articles):")
        for a in finnhub[:5]:
            title = a.get("title", "")
            content = a.get("content", "")
            line = f"  - {title}"
            if content:
                line += f"\n    {content[:200]}"
            parts.append(line)

    quote = data.get("quote")
    if quote:
        parts.append(f"\nMarket data ({quote.get('symbol', 'N/A')}):")
        parts.append(f"  Price: ${quote.get('current_price', 'N/A')}, "
                     f"Change: {quote.get('percent_change', 'N/A')}%, "
                     f"Range: ${quote.get('low', 'N/A')}-${quote.get('high', 'N/A')}")

    if not any(data.get(s) for s in ("news", "reddit", "twitter", "finnhub")):
        parts.append("\nNo recent media coverage found for this entity.")

    return "\n".join(parts)


def _synthesize_briefing(entity_name: str, scenario: str, raw_summary: str) -> str:
    """Use Claude to synthesize raw data into a concise research briefing."""
    if len(raw_summary) < 100:
        return raw_summary

    client = get_llm_client()
    prompt = SYNTHESIS_PROMPT.format(
        entity_name=entity_name,
        scenario=scenario,
        raw_data=raw_summary[:6000],
    )

    result = client.chat(
        messages=[{"role": "user", "content": prompt}],
        system="You are a concise research analyst. Write factual, data-driven briefings.",
        temperature=0.2,
        max_tokens=512,
    )
    return result.strip() if result else raw_summary
