
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.job import Job
from app.models.resume import Resume
from app.models.score import ATSScore
from app.models.skills import ResumeSkill, JobSkill
from app.models.company import Company
from app.models.job_source import JobSource
from sqlalchemy import text

async def clear_db():
    async with AsyncSessionLocal() as session:
        print("🗑️ Clearing Database...")
        await session.execute(text("TRUNCATE TABLE ats_scores CASCADE"))
        await session.execute(text("TRUNCATE TABLE resume_skills CASCADE"))
        await session.execute(text("TRUNCATE TABLE job_skills CASCADE"))
        await session.execute(text("TRUNCATE TABLE jobs CASCADE"))
        await session.execute(text("TRUNCATE TABLE resumes CASCADE"))
        await session.execute(text("TRUNCATE TABLE companies CASCADE"))
        await session.execute(text("TRUNCATE TABLE job_sources CASCADE"))
        await session.commit()
        print("✅ Database Cleared.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(clear_db())
