"""Neo4j graph schema setup for simulation knowledge graph.

Creates constraints, indexes (including vector indexes for semantic search),
and provides driver lifecycle management. Matches the full GraphRAG schema
from the integration plan.
"""

import threading

from neo4j import GraphDatabase

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('foresight.graph')

_driver = None
_driver_lock = threading.Lock()

# Cypher statements for schema initialization (idempotent)
SCHEMA_STATEMENTS = [
    # Uniqueness constraints
    "CREATE CONSTRAINT sim_id IF NOT EXISTS FOR (s:Simulation) REQUIRE s.simulation_id IS UNIQUE",
    "CREATE CONSTRAINT brand_id IF NOT EXISTS FOR (b:Brand) REQUIRE b.monitor_id IS UNIQUE",
    "CREATE CONSTRAINT scenario_type_unique IF NOT EXISTS FOR (st:ScenarioType) REQUIRE st.type IS UNIQUE",

    # Composite uniqueness for entities
    "CREATE CONSTRAINT entity_unique IF NOT EXISTS FOR (e:NamedEntity) REQUIRE (e.name, e.entity_type) IS UNIQUE",

    # Indexes for common lookups
    "CREATE INDEX action_sim_round IF NOT EXISTS FOR (a:Action) ON (a.simulation_id, a.round_num)",
    "CREATE INDEX action_id_idx IF NOT EXISTS FOR (a:Action) ON (a.action_id)",
    "CREATE INDEX agent_sim IF NOT EXISTS FOR (ag:AgentInstance) ON (ag.simulation_id, ag.agent_key)",
    "CREATE INDEX narrative_sim IF NOT EXISTS FOR (n:Narrative) ON (n.simulation_id)",
    "CREATE INDEX round_sim IF NOT EXISTS FOR (r:Round) ON (r.simulation_id, r.round_num)",
    "CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name)",
]

# Vector indexes for GraphRAG semantic retrieval
VECTOR_INDEX_STATEMENTS = [
    """CREATE VECTOR INDEX action_embedding IF NOT EXISTS
       FOR (a:Action) ON (a.embedding)
       OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}""",
    """CREATE VECTOR INDEX scenario_embedding IF NOT EXISTS
       FOR (s:Simulation) ON (s.scenario_embedding)
       OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}""",
    """CREATE VECTOR INDEX narrative_embedding IF NOT EXISTS
       FOR (n:Narrative) ON (n.embedding)
       OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}""",
    """CREATE VECTOR INDEX topic_embedding IF NOT EXISTS
       FOR (t:Topic) ON (t.embedding)
       OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}""",
]


def get_neo4j_driver():
    """Get or create singleton Neo4j driver."""
    global _driver
    if _driver is None:
        with _driver_lock:
            if _driver is None:
                if not Config.NEO4J_URI or not Config.NEO4J_PASSWORD:
                    raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be configured")
                _driver = GraphDatabase.driver(
                    Config.NEO4J_URI,
                    auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD),
                )
                _driver.verify_connectivity()
                logger.info(f"Neo4j driver connected to {Config.NEO4J_URI}")
    return _driver


def close_neo4j_driver():
    """Close the Neo4j driver."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


def init_graph_schema(driver=None):
    """Initialize graph schema with constraints and indexes. Idempotent."""
    driver = driver or get_neo4j_driver()
    db = Config.NEO4J_DATABASE or "neo4j"

    with driver.session(database=db) as session:
        for stmt in SCHEMA_STATEMENTS:
            try:
                session.run(stmt)
            except Exception as e:
                logger.warning(f"Schema statement skipped: {e}")

        for stmt in VECTOR_INDEX_STATEMENTS:
            try:
                session.run(stmt)
            except Exception as e:
                logger.warning(f"Vector index statement skipped: {e}")

    logger.info("Graph schema initialized (constraints + vector indexes)")
