
import asyncio
import os
import sys

# Ensure app in path
sys.path.append(os.getcwd())

from app.services.scraper.recursive_scraper import RecursiveScraper

async def test_scraper():
    print("Testing RecursiveScraper...")
    scraper = RecursiveScraper()
    print(f"Data Path: {scraper.data_path}")
    print(f"Exists? {os.path.exists(scraper.data_path)}")
    
    # Test fetch
    jobs = await scraper.fetch_jobs("*", "Dubai")
    print(f"Fetched {len(jobs)} jobs for query='*'")
    if jobs:
        print(f"Sample: {jobs[0]['title']}")

    # Test filtering
    jobs_py = await scraper.fetch_jobs("Python", "Dubai")
    print(f"Fetched {len(jobs_py)} jobs for query='Python'")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_scraper())
