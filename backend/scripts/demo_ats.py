import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.services.scoring.ats_logic import score_resume
from app.services.scraper.mock_scraper import MockScraper

async def run_demo():
    print("--- 1. Testing Scraper Logic ---")
    scraper = MockScraper("http://mock.url")
    jobs = await scraper.fetch_jobs("Python Backend", "Remote")
    print(f"Fetched {len(jobs)} raw jobs.")
    
    normalized = scraper.normalize_job(jobs[0])
    print(f"Normalized Job: {normalized.title} at {normalized.company_name}")
    print(f"Salary: {normalized.salary_min}-{normalized.salary_max} {normalized.currency}")
    
    print("\n--- 2. Testing ATS Scoring Logic ---")
    job_desc = """
    We are looking for a Senior Python Developer with experience in FastAPI, PostgreSQL, and Celery.
    Must have knowledge of Docker and AsyncIO.
    """
    
    resume_text = """
    John Doe
    Python Developer with 5 years of experience.
    Skilled in Django, Flask, and FastAPI.
    strong background in PostgreSQL and Docker.
    """
    
    print(f"Job Description Snippet: {job_desc.strip()}")
    print(f"Resume Snippet: {resume_text.strip()}")
    
    scores = score_resume(job_desc, resume_text)
    
    print("\n--- Scoring Results ---")
    print(f"Overall Score: {scores['overall_score']}")
    print(f"Keyword Score: {scores['keyword_score']}")
    print(f"Semantic Score: {scores['semantic_score']}")
    print(f"Missing Keywords: {scores['missing_keywords']['top_5']}")
    print(f"Matched Keywords: {scores['matched_keywords']['top_5']}")
    print(f"Insights: {scores['insights']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_demo())
