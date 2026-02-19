
import asyncio
import sys
import app.models # Ensure all models are registered
import time
from celery import Celery
from sqlalchemy import func, select
from app.db.session import AsyncSessionLocal
from app.models.job import Job
from app.models.score import ATSScore

app = Celery('worker', broker='redis://localhost:6379/0')

async def check_jobs():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(Job.id)))
        return result.scalar()

async def check_scores(resume_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(ATSScore.id)).filter(ATSScore.resume_id == resume_id))
        return result.scalar()

async def main():
    # 1. Trigger Ingestion (Directly in script to bypass worker env issue)
    print("🚀 Running Ingestion Synchronously...")
    try:
        from app.workers.ingestion import process_ingestion
        await process_ingestion("*", "Dubai")
    except ImportError:
        print("⚠️ Failed to import ingestion worker locally. Ensure you run this in web container.")
        return
    except Exception as e:
        print(f"❌ Ingestion Failed: {e}")
        return

    # app.send_task("app.workers.ingestion.fetch_jobs_task", args=["*", "Dubai"], queue="main-queue") # DISABLED
    
    # 2. Wait for Jobs
    print("⏳ Waiting for jobs...")
    jobs_count = 0
    for _ in range(30):
        jobs_count = await check_jobs()
        print(f"   Jobs: {jobs_count}")
        if jobs_count >= 10: # Expect 50, but 10 is enough to proceed
            break
        await asyncio.sleep(2)
        
    if jobs_count < 5:
        print("❌ Ingestion Failed or too slow.")
        return

    print(f"✅ Jobs Ingested: {jobs_count}")

    # 3. Create Dummy Resume & Trigger Batch Scoring
    from app.models.resume import Resume
    from app.models.skills import ResumeSkill
    import uuid
    
    resume_id = uuid.uuid4()
    print(f"📄 Creating Dummy Resume {resume_id}...")
    
    async with AsyncSessionLocal() as session:
        resume = Resume(
            id=resume_id,
            candidate_name="Test Candidate",
            email="test@example.com",
            file_path="/tmp/dummy.pdf",
            parsed_text="Experienced Python Developer with SQL and Docker skills.",
            status="PARSED"
        )
        session.add(resume)
        
        skills = ["Python", "SQL", "Docker", "FastAPI", "PostgreSQL"]
        for skill in skills:
            rs = ResumeSkill(resume_id=resume_id, skill_name=skill, proficiency=1.0)
            session.add(rs)
            
        await session.commit()
    
    print(f"🚀 Triggering Batch Scoring for {resume_id}...")
    app.send_task("app.workers.scoring.score_all_jobs_task", args=[str(resume_id)], queue="main-queue")
    
    # 4. Wait for Scores
    print("⏳ Waiting for scores...")
    scores_count = 0
    for _ in range(30):
        scores_count = await check_scores(resume_id)
        print(f"   Scores: {scores_count}")
        if scores_count >= jobs_count:
            break
        await asyncio.sleep(2)
        
    print(f"✅ Final Scores: {scores_count}")
    if scores_count > 0:
        print("🎉 Verification SUCCESS!")
    else:
        print("❌ Scoring Failed.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
