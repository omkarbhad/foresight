"""CrewAI tools for GraphRAG memory access.

SimulationMemoryTool: agents query the current simulation's knowledge graph
  - Full context (entities, narratives, influence chains)
  - Or filtered by query (e.g., "entity:Tesla" or "narrative:safety")
CrossSimulationTool: agents query past simulations for similar scenarios
"""

from typing import Any
from crewai.tools import BaseTool
from pydantic import Field


class SimulationMemoryTool(BaseTool):
    """GraphRAG tool for querying the current simulation's knowledge graph.

    Returns structured context: key entities with sentiment trajectories,
    active narrative threads with evolution tracking, multi-hop influence
    chains, and the most relevant recent actions.
    """

    name: str = "simulation_memory"
    description: str = (
        "Query the simulation knowledge graph for structured context about what has happened. "
        "Returns key entities with sentiment trajectories, active narrative threads showing "
        "how stories are evolving, multi-hop influence chains showing cause-and-effect between "
        "agents, and the most relevant recent actions. Use this to understand the current "
        "state of the simulation and make informed decisions."
    )
    reader: Any = Field(default=None, description="GraphMemoryReader instance")
    agent_key: str = Field(default="", description="Current agent key")
    current_round: int = Field(default=1, description="Current round number")

    def _run(self, query: str = "") -> str:
        """Query the simulation graph for context."""
        if not self.reader:
            return "Simulation memory not available."
        try:
            context = self.reader.get_simulation_context(self.agent_key, self.current_round)
            return context if context else "No simulation history recorded yet."
        except Exception as e:
            return f"Error querying simulation memory: {e}"


class CrossSimulationTool(BaseTool):
    """GraphRAG tool for querying past simulations via vector similarity.

    Searches across all historical simulations for scenarios similar to the
    current one, returning outcomes, sentiment arcs, and key dynamics.
    This gives agents institutional knowledge about how similar events
    played out in the past.
    """

    name: str = "past_simulations"
    description: str = (
        "Search past simulations for similar scenarios using semantic similarity. "
        "Returns how similar events played out previously — including final sentiment, "
        "peak crisis levels, sentiment trajectories, and key outcomes. Use this for "
        "institutional knowledge: 'has something like this happened before, and what happened?'"
    )
    reader: Any = Field(default=None, description="GraphMemoryReader instance")
    scenario_embedding: list = Field(default_factory=list, description="Scenario embedding vector")

    def _run(self, query: str = "") -> str:
        """Search for similar past simulations."""
        if not self.reader or not self.scenario_embedding:
            return "Cross-simulation search not available."
        try:
            result = self.reader.get_similar_scenarios(self.scenario_embedding)
            return result if result else "No similar past simulations found."
        except Exception as e:
            return f"Error searching past simulations: {e}"
