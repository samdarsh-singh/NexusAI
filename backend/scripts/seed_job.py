
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.job import Job
from app.models.company import Company
from app.models.job_source import JobSource
from uuid import uuid4
from datetime import datetime

async def seed():
    async with AsyncSessionLocal() as session:
        # Create Company
        company = Company(name="TechCorp Test", domain="techcorp.com")
        session.add(company)
        await session.flush()
        
        # Create Source
        source = JobSource(name="manual_seed", base_url="http://localhost")
        session.add(source)
        await session.flush()
        
        # Create Job
        job = Job(
            title="Senior Python Developer",
            company_id=company.id,
            source_id=source.id,
            external_id=str(uuid4()),
            location="Dubai, UAE",
            description_text="Looking for a Python expert with FastAPI and React experience.",
            salary_min=10000,
            salary_max=20000,
            currency="AED",
            posted_at=datetime.utcnow(),
            is_active=True,
            job_hash=str(uuid4())
        )
        session.add(job)
        await session.commit()
        print(f"Created Job: {job.id}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed())
