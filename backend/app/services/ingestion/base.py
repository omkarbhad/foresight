"""Base ingestion service ABC"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseIngestionService(ABC):
    @abstractmethod
    def fetch_mentions(self, keywords: List[str], negative_keywords: List[str] = None,
                       since: str = None) -> List[Dict[str, Any]]:
        """
        Fetch mentions matching keywords.

        Returns list of dicts with keys:
            source, source_url, title, content, author, published_at
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        pass
