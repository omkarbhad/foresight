"""CrewAI tools for simulation agents.

MediaLandscapeTool wraps the 90-day historical briefing so agents
can query it during their reasoning.
"""

from crewai.tools import BaseTool
from pydantic import Field


class MediaLandscapeTool(BaseTool):
    """Tool that provides agents with historical media landscape data."""

    name: str = "media_landscape"
    description: str = (
        "Access the media landscape briefing for this brand. Returns 90 days of "
        "historical data including sentiment trends, notable mentions, top topics, "
        "and source distribution. Use this to ground your response in real data."
    )
    briefing: str = Field(default="", description="The pre-loaded briefing text")

    def _run(self, query: str = "") -> str:
        """Return the full briefing. Query parameter is ignored — full context always returned."""
        if not self.briefing:
            return "No historical data available."
        return self.briefing
