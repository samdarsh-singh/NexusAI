from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseScraper(ABC):
    def __init__(self, base_url: str):
        self.base_url = base_url

    @abstractmethod
    async def fetch_jobs(self, query: str, location: str) -> List[Dict[str, Any]]:
        """
        Fetch jobs from the source.
        Returns a list of raw job dictionaries.
        """
        pass

    @abstractmethod
    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw job data into the standard JobCreate schema format.
        """
        pass
