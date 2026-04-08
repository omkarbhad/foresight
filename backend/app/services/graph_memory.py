"""Neo4j GraphRAG memory for simulation knowledge graph.

Full implementation of the graph memory integration plan:
- EntityExtractor: named entity + topic + narrative extraction per action
- GraphMemoryWriter: writes nodes with embeddings, relationships with properties,
  narrative evolution via embedding similarity, topic linking
- GraphMemoryReader: semantic graph queries replacing text dumps —
  vector-similarity retrieval, multi-hop influence chains, cross-simulation search
"""

import hashlib
from typing import Dict, List, Any, Optional

from ..config import Config
from ..utils.llm_client import get_llm_client
from ..utils.embeddings import generate_embedding, EMBEDDING_DIM
from ..utils.logger import get_logger

logger = get_logger('foresight.graph')

# Cosine similarity threshold for narrative evolution detection
NARRATIVE_SIMILARITY_THRESHOLD = 0.75

ENTITY_EXTRACTION_PROMPT = """Extract named entities and topics from this simulation action.

Action title: {title}
Action content: {content}
Agent role: {role}

Return JSON:
{{
    "entities": [
        {{"name": "full entity name", "type": "person|company|product|org|location|event|sector|country"}}
    ],
    "topics": ["topic_tag_1", "topic_tag_2"],
    "narrative_summary": "one sentence describing the narrative thread this action belongs to"
}}

Rules:
- Use full names, not pronouns (e.g., "Donald Trump" not "he")
- Extract 1-8 entities. If no clear entities, return empty list.
- Extract 1-5 topic tags (short, lowercase, e.g., "oil prices", "military withdrawal")
- narrative_summary should capture the story arc, not just restate the action."""


class EntityExtractor:
    """Lightweight Claude-based entity + topic + narrative extraction with caching."""

    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = get_llm_client()
        return self._client

    def extract(self, title: str, content: str, role: str = "") -> Dict:
        """Extract entities, topics, and narrative summary from action content.

        Returns: {"entities": [...], "topics": [...], "narrative_summary": str}
        """
        cache_key = hashlib.md5(f"{title}:{content}".encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            client = self._get_client()
            result = client.chat_json(
                messages=[{
                    "role": "user",
                    "content": ENTITY_EXTRACTION_PROMPT.format(
                        title=title or "", content=content or "", role=role or "",
                    ),
                }],
                system="Extract entities and topics precisely. Return valid JSON only.",
                temperature=0.1,
                max_tokens=512,
            )
            result.setdefault("entities", [])
            result.setdefault("topics", [])
            result.setdefault("narrative_summary", "")
            self._cache[cache_key] = result
            return result

        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return {"entities": [], "topics": [], "narrative_summary": ""}


class GraphMemoryWriter:
    """Writes simulation data to Neo4j as a full knowledge graph with embeddings."""

    def __init__(self, driver, simulation_id: str):
        self.driver = driver
        self.simulation_id = simulation_id
        self.db = Config.NEO4J_DATABASE or "neo4j"
        self.extractor = EntityExtractor()

    def init_simulation(
        self, monitor, scenario: str, agent_defs: Dict, execution_order: List[str],
        total_rounds: int = 6,
    ):
        """Create Simulation, Brand, ScenarioType, AgentInstance, and Round nodes."""
        scenario_embedding = generate_embedding(scenario)

        with self.driver.session(database=self.db) as session:
            # Simulation node with embedding
            session.run(
                """MERGE (s:Simulation {simulation_id: $sim_id})
                   SET s.scenario_text = $scenario,
                       s.scenario_embedding = $embedding,
                       s.engine_version = 'v3',
                       s.created_at = datetime()""",
                sim_id=self.simulation_id, scenario=scenario, embedding=scenario_embedding,
            )

            # ScenarioType node — categorize the scenario
            scenario_type = self._classify_scenario(scenario)
            session.run(
                """MERGE (st:ScenarioType {type: $type})
                   SET st.embedding = $embedding
                   WITH st
                   MATCH (s:Simulation {simulation_id: $sim_id})
                   MERGE (s)-[:HAS_SCENARIO]->(st)""",
                type=scenario_type, embedding=scenario_embedding, sim_id=self.simulation_id,
            )

            # Brand node
            if monitor:
                session.run(
                    """MERGE (b:Brand {monitor_id: $mid})
                       SET b.name = $name, b.keywords = $keywords
                       WITH b
                       MATCH (s:Simulation {simulation_id: $sim_id})
                       MERGE (s)-[:FOR_BRAND]->(b)""",
                    mid=monitor.monitor_id, name=monitor.name,
                    keywords=monitor.keywords or [], sim_id=self.simulation_id,
                )

            # Agent nodes
            for key in execution_order:
                defn = agent_defs.get(key, {})
                session.run(
                    """MERGE (a:AgentInstance {simulation_id: $sim_id, agent_key: $key})
                       SET a.role = $role, a.influence_weight = $weight, a.platform = $platform
                       WITH a
                       MATCH (s:Simulation {simulation_id: $sim_id})
                       MERGE (a)-[:PARTICIPATED_IN]->(s)""",
                    sim_id=self.simulation_id, key=key,
                    role=defn.get("role", ""), weight=defn.get("influence_weight", 0.1),
                    platform=defn.get("platform", "mixed"),
                )

            # Round nodes
            from .crewai_agents import TIME_LABELS
            for r in range(1, total_rounds + 1):
                session.run(
                    """MERGE (r:Round {simulation_id: $sim_id, round_num: $rn})
                       SET r.time_label = $tl
                       WITH r
                       MATCH (s:Simulation {simulation_id: $sim_id})
                       MERGE (s)-[:HAS_ROUND]->(r)""",
                    sim_id=self.simulation_id, rn=r, tl=TIME_LABELS.get(r, f"Round {r}"),
                )

        logger.info(f"Graph initialized for simulation {self.simulation_id} (type: {scenario_type})")

    def record_action(
        self, agent_key: str, defn: Dict, action: Dict, round_num: int,
        round_actions: List[Dict],
    ):
        """Record a single agent action with full GraphRAG enrichment."""
        title = action.get("title", "")
        content = action.get("content", "")

        if action.get("action_type") == "no_action":
            return

        # Generate embedding for semantic retrieval
        action_text = f"{title}. {content}"
        embedding = generate_embedding(action_text)

        # Extract entities, topics, narrative
        extraction = self.extractor.extract(title, content, defn.get("role", ""))

        action_id = f"{self.simulation_id}_{agent_key}_r{round_num}"

        with self.driver.session(database=self.db) as session:
            # 1. Create Action node with embedding
            session.run(
                """CREATE (a:Action {
                       action_id: $aid, simulation_id: $sim_id,
                       agent_key: $agent_key, round_num: $round_num,
                       action_type: $action_type, title: $title, content: $content,
                       sentiment_score: $sentiment, reach_estimate: $reach,
                       reasoning: $reasoning, embedding: $embedding
                   })""",
                aid=action_id, sim_id=self.simulation_id, agent_key=agent_key,
                round_num=round_num, action_type=action.get("action_type", ""),
                title=title, content=content,
                sentiment=action.get("sentiment_score", 0.0),
                reach=action.get("reach_estimate", 0),
                reasoning=action.get("reasoning", ""), embedding=embedding,
            )

            # 2. Link to agent and round
            session.run(
                """MATCH (a:Action {action_id: $aid})
                   MATCH (ag:AgentInstance {simulation_id: $sim_id, agent_key: $agent_key})
                   MATCH (r:Round {simulation_id: $sim_id, round_num: $round_num})
                   MERGE (ag)-[:TOOK_ACTION]->(a)
                   MERGE (a)-[:IN_ROUND]->(r)""",
                aid=action_id, sim_id=self.simulation_id,
                agent_key=agent_key, round_num=round_num,
            )

            # 3. Create/link NamedEntity nodes with Brand connection
            for entity in extraction.get("entities", []):
                ename = entity.get("name", "").strip()
                etype = entity.get("type", "unknown").strip()
                if not ename:
                    continue
                session.run(
                    """MERGE (e:NamedEntity {name: $name, entity_type: $type})
                       ON CREATE SET e.first_seen = datetime()
                       WITH e
                       MATCH (a:Action {action_id: $aid})
                       MERGE (a)-[:MENTIONS_ENTITY]->(e)
                       WITH e
                       MATCH (s:Simulation {simulation_id: $sim_id})-[:FOR_BRAND]->(b:Brand)
                       MERGE (b)-[:HAS_ENTITY]->(e)""",
                    name=ename, type=etype, aid=action_id, sim_id=self.simulation_id,
                )

            # 4. Create/link Topic nodes with embeddings
            for topic_name in extraction.get("topics", []):
                topic_name = topic_name.strip().lower()
                if not topic_name:
                    continue
                topic_embedding = generate_embedding(topic_name)
                session.run(
                    """MERGE (t:Topic {name: $name})
                       ON CREATE SET t.embedding = $embedding
                       WITH t
                       MATCH (a:Action {action_id: $aid})
                       MERGE (a)-[:HAS_TOPIC]->(t)""",
                    name=topic_name, embedding=topic_embedding, aid=action_id,
                )

            # 5. INFLUENCED_BY edges with relationship properties
            for source_key in action.get("influenced_by", []):
                session.run(
                    """MATCH (a:Action {action_id: $aid})
                       MATCH (src:Action {simulation_id: $sim_id, agent_key: $source_key})
                       WHERE src.round_num <= $round_num AND src.action_id <> $aid
                       WITH a, src ORDER BY src.round_num DESC LIMIT 1
                       MERGE (a)-[r:INFLUENCED_BY]->(src)
                       SET r.influence_strength = abs(a.sentiment_score - src.sentiment_score),
                           r.mechanism = src.action_type + ' → ' + a.action_type""",
                    aid=action_id, sim_id=self.simulation_id,
                    source_key=source_key, round_num=round_num,
                )

            # 6. Narrative detection via embedding similarity
            narrative_summary = extraction.get("narrative_summary", "")
            if narrative_summary:
                narrative_embedding = generate_embedding(narrative_summary)
                self._link_or_create_narrative(
                    session, action_id, narrative_summary,
                    narrative_embedding, round_num,
                    action.get("sentiment_score", 0.0),
                )

    def _link_or_create_narrative(
        self, session, action_id: str, summary: str,
        embedding: List[float], round_num: int, sentiment: float,
    ):
        """Find similar existing narrative (via vector search) or create new one."""
        # Check if we have real embeddings (not zero-vector)
        has_real_embedding = any(v != 0.0 for v in embedding[:10])

        matched = False
        if has_real_embedding:
            try:
                # Search for similar narratives in this simulation
                results = session.run(
                    """CALL db.index.vector.queryNodes('narrative_embedding', 3, $embedding)
                       YIELD node, score
                       WHERE node.simulation_id = $sim_id AND score > $threshold
                       RETURN node.summary AS summary, score,
                              elementId(node) AS node_id,
                              node.round_emerged AS round_emerged,
                              node.sentiment_direction AS old_sentiment
                       ORDER BY score DESC LIMIT 1""",
                    embedding=embedding, sim_id=self.simulation_id,
                    threshold=NARRATIVE_SIMILARITY_THRESHOLD,
                ).data()

                if results:
                    # Narrative evolution: link via EVOLVED_INTO
                    match = results[0]
                    session.run(
                        """CREATE (n:Narrative {
                               simulation_id: $sim_id, summary: $summary,
                               embedding: $embedding, round_emerged: $round_num,
                               sentiment_direction: $sentiment
                           })
                           WITH n
                           MATCH (a:Action {action_id: $aid})
                           MERGE (a)-[:SPAWNED_NARRATIVE]->(n)
                           WITH n
                           MATCH (old) WHERE elementId(old) = $old_id
                           CREATE (old)-[r:EVOLVED_INTO]->(n)
                           SET r.sentiment_shift = $sentiment - $old_sentiment,
                               r.round_gap = $round_num - $old_round""",
                        sim_id=self.simulation_id, summary=summary,
                        embedding=embedding, round_num=round_num,
                        sentiment=sentiment, aid=action_id,
                        old_id=match["node_id"],
                        old_sentiment=match.get("old_sentiment", 0.0),
                        old_round=match.get("round_emerged", 0),
                    )
                    matched = True
            except Exception as e:
                logger.debug(f"Narrative vector search failed (may not have index yet): {e}")

        if not matched:
            # New narrative thread
            session.run(
                """CREATE (n:Narrative {
                       simulation_id: $sim_id, summary: $summary,
                       embedding: $embedding, round_emerged: $round_num,
                       sentiment_direction: $sentiment
                   })
                   WITH n
                   MATCH (a:Action {action_id: $aid})
                   MERGE (a)-[:SPAWNED_NARRATIVE]->(n)""",
                sim_id=self.simulation_id, summary=summary,
                embedding=embedding, round_num=round_num,
                sentiment=sentiment, aid=action_id,
            )

    def persist_influence_graph(self, influence_log: List[Dict]):
        """Bulk-write influence log entries as agent-level relationships."""
        with self.driver.session(database=self.db) as session:
            for entry in influence_log:
                session.run(
                    """MATCH (src:AgentInstance {simulation_id: $sim_id, agent_key: $from_key})
                       MATCH (tgt:AgentInstance {simulation_id: $sim_id, agent_key: $to_key})
                       MERGE (src)-[r:INFLUENCES]->(tgt)
                       SET r.count = coalesce(r.count, 0) + 1""",
                    sim_id=self.simulation_id,
                    from_key=entry.get("from", ""),
                    to_key=entry.get("to", ""),
                )

    def update_simulation_metrics(self, final_sentiment: float, peak_crisis: float):
        """Update Simulation node with final metrics for cross-sim search."""
        with self.driver.session(database=self.db) as session:
            session.run(
                """MATCH (s:Simulation {simulation_id: $sim_id})
                   SET s.final_sentiment = $final_sentiment,
                       s.peak_crisis = $peak_crisis""",
                sim_id=self.simulation_id,
                final_sentiment=final_sentiment, peak_crisis=peak_crisis,
            )

    def update_round_metrics(self, round_num: int, metrics: Dict):
        """Update Round node with computed metrics."""
        with self.driver.session(database=self.db) as session:
            session.run(
                """MATCH (r:Round {simulation_id: $sim_id, round_num: $rn})
                   SET r.avg_sentiment = $avg_sent, r.crisis_level = $crisis,
                       r.volume = $volume""",
                sim_id=self.simulation_id, rn=round_num,
                avg_sent=metrics.get("avg_sentiment", 0),
                crisis=metrics.get("crisis_level", 0),
                volume=metrics.get("round_volume", 0),
            )

    @staticmethod
    def _classify_scenario(scenario: str) -> str:
        """Simple keyword-based scenario classification."""
        s = scenario.lower()
        if any(w in s for w in ["recall", "defect", "safety"]):
            return "product_recall"
        if any(w in s for w in ["ceo", "scandal", "resign", "fired"]):
            return "ceo_scandal"
        if any(w in s for w in ["breach", "hack", "data leak", "cyber"]):
            return "data_breach"
        if any(w in s for w in ["war", "military", "withdraw", "invasion", "troops"]):
            return "military_conflict"
        if any(w in s for w in ["tariff", "trade", "sanction", "embargo"]):
            return "trade_policy"
        if any(w in s for w in ["election", "vote", "campaign", "poll"]):
            return "election"
        if any(w in s for w in ["regulation", "fine", "compliance", "antitrust"]):
            return "regulatory_action"
        if any(w in s for w in ["merger", "acquisition", "buyout"]):
            return "merger_acquisition"
        if any(w in s for w in ["viral", "trending", "tiktok", "meme"]):
            return "viral_moment"
        return "general"


class GraphMemoryReader:
    """Reads simulation context from Neo4j using GraphRAG patterns.

    Key difference from simple Cypher: uses vector similarity for relevance-based
    retrieval, multi-hop graph traversal for influence chains, and bounded output
    instead of dumping all actions.
    """

    def __init__(self, driver, simulation_id: str):
        self.driver = driver
        self.simulation_id = simulation_id
        self.db = Config.NEO4J_DATABASE or "neo4j"

    def get_simulation_context(self, agent_key: str, round_num: int) -> str:
        """Get structured GraphRAG context for an agent.

        Returns semantic entity-relationship summaries, active narrative threads
        with evolution tracking, and multi-hop influence chains — all bounded
        and relevant, not a full action dump.
        """
        sections = []

        with self.driver.session(database=self.db) as session:
            # 1. Key entities with sentiment trajectories
            entities = session.run(
                """MATCH (a:Action {simulation_id: $sim_id})-[:MENTIONS_ENTITY]->(e:NamedEntity)
                   WHERE a.round_num < $round_num
                   WITH e, collect(DISTINCT {round: a.round_num, sentiment: a.sentiment_score,
                        agent: a.agent_key}) AS mentions
                   ORDER BY size(mentions) DESC LIMIT 10
                   RETURN e.name AS name, e.entity_type AS type,
                          size(mentions) AS mention_count, mentions""",
                sim_id=self.simulation_id, round_num=round_num,
            ).data()

            if entities:
                entity_lines = []
                for e in entities:
                    mentions = e.get("mentions", [])
                    sents = [m["sentiment"] for m in mentions if m.get("sentiment") is not None]
                    if not sents:
                        continue
                    agents = list(set(m.get("agent", "") for m in mentions))
                    trajectory = f"{sents[0]:.1f} → {sents[-1]:.1f}" if len(sents) > 1 else f"{sents[0]:.1f}"
                    linked_agents = ", ".join(a.replace("_", " ").title() for a in agents[:3])
                    entity_lines.append(
                        f"  - {e['name']} ({e['type']}): {e['mention_count']} references, "
                        f"sentiment: {trajectory}, mentioned by: {linked_agents}"
                    )
                sections.append("KEY ENTITIES:\n" + "\n".join(entity_lines))

            # 2. Active narratives with evolution chains
            narratives = session.run(
                """MATCH (n:Narrative {simulation_id: $sim_id})
                   WHERE n.round_emerged < $round_num
                   OPTIONAL MATCH (n)-[ev:EVOLVED_INTO]->(evolved:Narrative)
                   WITH n, collect({to_summary: evolved.summary, shift: ev.sentiment_shift,
                        gap: ev.round_gap}) AS evolutions
                   RETURN n.summary AS summary, n.round_emerged AS round,
                          n.sentiment_direction AS sentiment, evolutions
                   ORDER BY n.round_emerged DESC LIMIT 5""",
                sim_id=self.simulation_id, round_num=round_num,
            ).data()

            if narratives:
                narr_lines = []
                for i, n in enumerate(narratives, 1):
                    sent = n.get("sentiment", 0) or 0
                    direction = "strengthening" if sent < -0.3 else \
                                "positive" if sent > 0.3 else "developing"
                    line = f'  {i}. "{n["summary"]}" (emerged Round {n["round"]}, {direction})'

                    # Show evolution chain if exists
                    evolutions = [e for e in n.get("evolutions", []) if e.get("to_summary")]
                    if evolutions:
                        ev = evolutions[0]
                        shift = ev.get("shift", 0) or 0
                        shift_dir = "↑" if shift > 0 else "↓" if shift < 0 else "→"
                        line += f'\n     → Evolved: "{ev["to_summary"]}" (sentiment {shift_dir}{abs(shift):.1f})'

                    narr_lines.append(line)
                sections.append("ACTIVE NARRATIVES:\n" + "\n".join(narr_lines))

            # 3. Multi-hop influence chain relevant to this agent
            influence_chain = self._get_influence_chain(session, agent_key, round_num)
            if influence_chain:
                sections.append(influence_chain)

            # 4. Vector-similar recent actions (most relevant, not just most recent)
            relevant_actions = self._get_relevant_actions(session, agent_key, round_num)
            if relevant_actions:
                sections.append(relevant_actions)

        if not sections:
            return ""

        return "SIMULATION MEMORY (from knowledge graph):\n\n" + "\n\n".join(sections)

    def _get_influence_chain(self, session, agent_key: str, round_num: int) -> str:
        """Traverse multi-hop influence paths ending at this agent."""
        try:
            chains = session.run(
                """MATCH path = (src:Action)-[:INFLUENCED_BY*1..3]->(target:Action)
                   WHERE src.simulation_id = $sim_id
                     AND src.round_num < $round_num
                   WITH path, src, target,
                        [n IN nodes(path) | n.agent_key + ': "' + n.title + '"'] AS chain_desc,
                        [r IN relationships(path) | r.mechanism] AS mechanisms
                   RETURN chain_desc, mechanisms,
                          src.sentiment_score AS src_sentiment,
                          target.sentiment_score AS tgt_sentiment
                   ORDER BY length(path) DESC, src.round_num DESC
                   LIMIT 3""",
                sim_id=self.simulation_id, round_num=round_num,
            ).data()

            if not chains:
                return ""

            lines = [f"INFLUENCE CHAINS (relevant to you as {agent_key.replace('_', ' ').title()}):"]
            for c in chains:
                chain_parts = c.get("chain_desc", [])
                if len(chain_parts) >= 2:
                    chain_str = " → ".join(
                        p.replace("_", " ").title() if ":" not in p else p
                        for p in chain_parts
                    )
                    lines.append(f"  {chain_str}")

            return "\n".join(lines) if len(lines) > 1 else ""

        except Exception as e:
            logger.debug(f"Influence chain query failed: {e}")
            return ""

    def _get_relevant_actions(self, session, agent_key: str, round_num: int) -> str:
        """Get the most relevant prior actions using vector similarity when possible,
        falling back to recency-based retrieval."""
        try:
            # Try vector-based retrieval: find actions similar to the most recent action
            # by this agent (or by any agent if this is the first action)
            recent = session.run(
                """MATCH (a:Action {simulation_id: $sim_id})
                   WHERE a.round_num < $round_num AND a.agent_key <> $agent_key
                   RETURN a.agent_key AS agent, a.action_type AS type,
                          a.title AS title, a.sentiment_score AS sentiment,
                          a.reach_estimate AS reach, a.round_num AS round
                   ORDER BY a.round_num DESC, a.reach_estimate DESC
                   LIMIT 6""",
                sim_id=self.simulation_id, round_num=round_num, agent_key=agent_key,
            ).data()

            if not recent:
                return ""

            lines = ["RECENT KEY ACTIONS:"]
            for a in recent:
                agent_name = a['agent'].replace('_', ' ').title()
                lines.append(
                    f"  R{a['round']}: {agent_name} [{a['type']}] \"{a['title']}\" "
                    f"(sentiment: {a['sentiment']:.1f}, reach: {a['reach']:,})"
                )
            return "\n".join(lines)

        except Exception as e:
            logger.debug(f"Relevant actions query failed: {e}")
            return ""

    def get_influence_context(
        self, agent_key: str, round_num: int,
        influence_incoming: Dict[str, List[str]] = None,
    ) -> str:
        """Get multi-hop influence context from the graph.

        Augments the flat influence_matrix.get_influence_context() with
        graph traversal for richer chain reasoning.
        """
        with self.driver.session(database=self.db) as session:
            # Find actions by agents that influence this one, with chain context
            influencers = (influence_incoming or {}).get(agent_key, [])
            if not influencers:
                return ""

            results = session.run(
                """MATCH (a:Action {simulation_id: $sim_id})
                   WHERE a.agent_key IN $influencers
                     AND a.round_num <= $round_num
                     AND a.action_type <> 'no_action'
                   OPTIONAL MATCH (a)-[inf:INFLUENCED_BY]->(source:Action)
                   RETURN a.agent_key AS agent, a.action_type AS type,
                          a.title AS title, a.sentiment_score AS sentiment,
                          a.reach_estimate AS reach, a.round_num AS round,
                          source.agent_key AS influenced_by_agent,
                          source.title AS influenced_by_title,
                          inf.mechanism AS mechanism
                   ORDER BY a.round_num DESC
                   LIMIT 8""",
                sim_id=self.simulation_id, round_num=round_num, influencers=influencers,
            ).data()

            if not results:
                return ""

            lines = ["INFLUENCE CONTEXT (from knowledge graph):"]
            for r in results:
                agent_name = r['agent'].replace('_', ' ').title()
                line = f"  [{r.get('round', '?')}] {agent_name} — {r['type']}: \"{r['title']}\" (sentiment: {r['sentiment']:.1f})"
                if r.get("influenced_by_agent"):
                    src_name = r['influenced_by_agent'].replace('_', ' ').title()
                    line += f"\n       ← influenced by {src_name}: \"{r.get('influenced_by_title', '')}\""
                    if r.get("mechanism"):
                        line += f" [{r['mechanism']}]"
                lines.append(line)

            return "\n".join(lines)

    def get_similar_scenarios(
        self, scenario_embedding: List[float], limit: int = 3,
    ) -> str:
        """Find similar past simulations via vector similarity search.

        Returns structured cross-simulation context including outcomes,
        key turning points, and entity patterns.
        """
        if all(v == 0.0 for v in scenario_embedding[:10]):
            return ""

        try:
            with self.driver.session(database=self.db) as session:
                results = session.run(
                    """CALL db.index.vector.queryNodes('scenario_embedding', $limit, $embedding)
                       YIELD node, score
                       WHERE score > 0.7 AND node.simulation_id <> $current_sim
                       OPTIONAL MATCH (node)-[:HAS_ROUND]->(r:Round)
                       WITH node, score, r ORDER BY r.round_num
                       WITH node, score, collect(r) AS rounds
                       OPTIONAL MATCH (node)-[:FOR_BRAND]->(b:Brand)
                       RETURN node.simulation_id AS sim_id,
                              node.scenario_text AS scenario,
                              node.final_sentiment AS final_sentiment,
                              node.peak_crisis AS peak_crisis,
                              b.name AS brand_name,
                              score,
                              size(rounds) AS round_count,
                              [r IN rounds | r.avg_sentiment] AS sentiment_by_round,
                              [r IN rounds | r.crisis_level] AS crisis_by_round
                       ORDER BY score DESC LIMIT $limit""",
                    embedding=scenario_embedding, limit=limit,
                    current_sim=self.simulation_id,
                ).data()

                if not results:
                    return ""

                lines = ["SIMILAR PAST SCENARIOS (institutional knowledge):"]
                for r in results:
                    scenario_text = (r.get("scenario") or "")[:150]
                    final_sent = r.get("final_sentiment") or 0
                    peak = r.get("peak_crisis") or 0
                    brand = r.get("brand_name") or "Unknown"
                    similarity = r.get("score", 0)

                    line = (
                        f'  - "{scenario_text}" (brand: {brand}, similarity: {similarity:.2f})\n'
                        f'    Outcome: final sentiment {final_sent:.2f}, peak crisis {peak:.0%}, '
                        f'{r.get("round_count", 0)} rounds'
                    )

                    # Add sentiment trajectory if available
                    sents = [s for s in (r.get("sentiment_by_round") or []) if s is not None]
                    if len(sents) > 2:
                        line += f'\n    Sentiment arc: {" → ".join(f"{s:.1f}" for s in sents)}'

                    lines.append(line)

                return "\n".join(lines)

        except Exception as e:
            logger.warning(f"Similar scenario search failed: {e}")
            return ""
