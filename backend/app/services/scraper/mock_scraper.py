from typing import List, Dict, Any
from datetime import datetime
import uuid
import random

from app.services.scraper.base import BaseScraper
from app.schemas.job import JobCreate

class MockScraper(BaseScraper):
    """
    Simulates scraping data from a job site like LinkedIn or Indeed.
    Useful for testing without hitting rate limits or needing real proxies.
    """
    
    async def fetch_jobs(self, query: str, location: str) -> List[Dict[str, Any]]:
        # Simulate network delay?
        # await asyncio.sleep(1)
        
        results = []
        for i in range(5):
            results.append({
                "external_id": str(uuid.uuid4()),
                "title": f"{query} Developer - {i+1}",
                "company": f"Tech Corp {random.randint(1, 100)}",
                "location": location,
                "description": f"We are looking for a {query} expert...",
                "salary": f"{random.randint(80, 150)}k",
                "posted_date": datetime.now().isoformat(),
                "url": f"https://example.com/job/{i}"
            })
        return results

    def normalize_job(self, raw_job: Dict[str, Any]) -> JobCreate:
        return JobCreate(
            title=raw_job["title"],
            company_name=raw_job["company"],
            location=raw_job["location"],
            description_text=raw_job["description"],
            salary_min=80000, # Mock parsing
            salary_max=150000,
            currency="USD",
            external_id=raw_job["external_id"],
            source_name="mock_source",
            source_url=raw_job["url"],
            posted_at=datetime.fromisoformat(raw_job["posted_date"])
        )
