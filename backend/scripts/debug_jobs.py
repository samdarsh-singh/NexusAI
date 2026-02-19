
import asyncio
from sqlalchemy import func
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.models.job import Job

async def count_jobs():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(Job.id)))
        count = result.scalar()
        print(f"Total Jobs in DB: {count}")
        
        # List first 3 titles
        result = await session.execute(select(Job).limit(3))
        jobs = result.scalars().all()
        for job in jobs:
            print(f"- {job.title} ({job.company_id})")
            
        # Count Resumes
        from app.models.resume import Resume
        res_result = await session.execute(select(Resume))
        resumes = res_result.scalars().all()
        print(f"\nTotal Resumes: {len(resumes)}")
        for res in resumes:
            print(f"- {res.candidate_name} (ID: {res.id})")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(count_jobs())
