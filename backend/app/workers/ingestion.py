import asyncio
import hashlib
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.db.mongodb import mongo_db
from app.services.scraper.recursive_scraper import RecursiveScraper
from app.models.job import Job
from app.models.company import Company
from app.models.job_source import JobSource
from app.schemas.job import JobCreate

async def save_raw_job_to_mongo(raw_job: Dict[str, Any], source: str):
    # Ensure connection
    if not mongo_db.client:
        mongo_db.connect()
    
    db = mongo_db.db
    await db.raw_job_posts.insert_one({
        "source": source,
        "scraped_at": datetime.utcnow(),
        "raw_data": raw_job
    })

async def get_or_create_company(session: AsyncSession, name: str) -> Company:
    result = await session.execute(select(Company).filter(Company.name == name))
    company = result.scalars().first()
    if not company:
        company = Company(name=name)
        session.add(company)
        await session.flush()
    return company

async def get_or_create_source(session: AsyncSession, name: str) -> JobSource:
    result = await session.execute(select(JobSource).filter(JobSource.name == name))
    source = result.scalars().first()
    if not source:
        source = JobSource(name=name)
        session.add(source)
        await session.flush()
    return source

def generate_job_hash(title: str, company_name: str, location: str) -> str:
    s = f"{title.lower()}|{company_name.lower()}|{location.lower()}"
    return hashlib.md5(s.encode()).hexdigest()

async def ingest_job(session: AsyncSession, job_data: JobCreate):
    # Check deduplication
    job_hash = generate_job_hash(job_data.title, job_data.company_name, job_data.location)
    
    # We use a simplified check here. In production, we might want to update existing jobs.
    existing = await session.execute(select(Job).filter(Job.job_hash == job_hash))
    if existing.scalars().first():
        # print(f"Skipping duplicate job: {job_data.title} at {job_data.company_name}")
        return

    company = await get_or_create_company(session, job_data.company_name)
    source = await get_or_create_source(session, job_data.source_name)

    new_job = Job(
        title=job_data.title,
        company_id=company.id,
        source_id=source.id,
        external_id=job_data.external_id,
        location=job_data.location,
        description_text=job_data.description_text,
        salary_min=job_data.salary_min,
        salary_max=job_data.salary_max,
        currency=job_data.currency,
        posted_at=job_data.posted_at.replace(tzinfo=None) if job_data.posted_at else datetime.utcnow(), # Ensure naive/utc match
        job_hash=job_hash
    )
    session.add(new_job)
    await session.commit()
    await session.refresh(new_job)

    # Extract and Save Skills
    import re
    from app.core.constants import SKILL_KEYWORDS
    from app.models.skills import JobSkill
    
    description_lower = job_data.description_text.lower() if job_data.description_text else ""
    title_lower = job_data.title.lower() if job_data.title else ""
    text_corpus = f"{title_lower} {description_lower}"

    for skill in SKILL_KEYWORDS:
        if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_corpus):
             job_skill = JobSkill(
                 job_id=new_job.id,
                 skill_name=skill,
                 weight=1.0 
             )
             session.add(job_skill)
    
    await session.commit()
    print(f"Ingested Job: {new_job.title} from {job_data.source_name}")

async def process_ingestion(query: str, location: str):
    scraper = RecursiveScraper()
    # Fetch
    print(f"Fetching jobs for {query} in {location}...")
    raw_jobs = await scraper.fetch_jobs(query, location)
    print(f"Found {len(raw_jobs)} jobs.")
    
    async with AsyncSessionLocal() as session:
        for raw in raw_jobs:
            # 1. Normalize
            normalized_job = scraper.normalize_job(raw)
            
            # 2. Save Raw to Mongo (using normalized source name)
            await save_raw_job_to_mongo(raw, normalized_job.source_name)
            
            # 3. Save to Postgres
            await ingest_job(session, normalized_job)

@celery_app.task
def fetch_jobs_task(query: str, location: str):
    """
    Celery task wrapper for async ingestion.
    """
    import asyncio
    
    # We need to run the async function in a new loop
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(process_ingestion(query, location))
    return f"Ingested jobs for {query} in {location}"
