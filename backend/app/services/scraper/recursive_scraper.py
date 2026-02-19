
import json
import os
import uuid
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.services.scraper.base import BaseScraper
from app.schemas.job import JobCreate

class RecursiveScraper(BaseScraper):
    """
    Simulates a high-fidelity Recursive Scraper that 'crawls' sources
    by loading a curated realistic dataset.
    """
    
    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(__file__), 'data', 'dubai_tech_jobs.json')
        self._cache = None
        
    def _load_data(self) -> List[Dict[str, Any]]:
        if self._cache:
            return self._cache
            
        if not os.path.exists(self.data_path):
             # Fallback if file missing
             return []
             
        with open(self.data_path, 'r') as f:
            self._cache = json.load(f)
        return self._cache

    async def fetch_jobs(self, query: str, location: str) -> List[Dict[str, Any]]:
        """
        Fetches jobs from the dataset, filtering by query and location to simulate a search engine.
        """
        all_jobs = self._load_data()
        
        # Simple fuzzy filtering
        filtered_jobs = []
        query_terms = query.lower().split()
        location_term = location.lower()
        # Special case: "*" returns all jobs for bulk ingestion
        if query == "*":
            # Add dynamic metadata to all
            for job in all_jobs:
                 job_copy = job.copy()
                 job_copy['external_id'] = str(uuid.uuid4())
                 days_ago = random.randint(0, 5)
                 job_copy['posted_at'] = (datetime.now() - timedelta(days=days_ago)).isoformat()
                 filtered_jobs.append(job_copy)
            return filtered_jobs

        for job in all_jobs:
            # Check Location (loose match)
            if location_term in job['location'].lower() or 'uae' in location_term or location == "*":
                # Check Query (at least one term match in title or description)
                text_corpus = (job['title'] + " " + job['description']).lower()
                if any(term in text_corpus for term in query_terms):
                    # Add dynamic metadata to make it look live
                    job_copy = job.copy()
                    job_copy['external_id'] = str(uuid.uuid4())
                    # Jitter posted date slightly to look like live feed
                    days_ago = random.randint(0, 3)
                    job_copy['posted_at'] = (datetime.now() - timedelta(days=days_ago)).isoformat()
                    filtered_jobs.append(job_copy)
        
        # If no match, return all (fallback behavior for generic queries) or empty
        # For demo purposes, if query is generic like "developer", return a mix
        if not filtered_jobs and ("dev" in query.lower() or " engineer" in query.lower()):
            return all_jobs[:5] # Return top 5 as fallback
            
        return filtered_jobs

    def normalize_job(self, raw_job: Dict[str, Any]) -> JobCreate:
        salary_str = raw_job.get('salary', '0')
        # Very basic parsing for demo data "AED 25,000 - 35,000"
        min_sal = 0
        max_sal = 0
        try:
            nums = [int(s.replace(',', '')) for s in salary_str.split() if s.replace(',', '').isdigit()]
            if nums:
                min_sal = min(nums)
                max_sal = max(nums)
        except:
            pass

        return JobCreate(
            title=raw_job["title"],
            company_name=raw_job["company"],
            location=raw_job["location"],
            description_text=raw_job["description"],
            salary_min=min_sal,
            salary_max=max_sal,
            currency="AED",
            external_id=raw_job.get("external_id", str(uuid.uuid4())),
            source_name=raw_job.get("source", "Aggregator"),
            source_url="#", # Placeholder
            posted_at=datetime.fromisoformat(str(raw_job.get("posted_at", datetime.now().isoformat())))
        )
