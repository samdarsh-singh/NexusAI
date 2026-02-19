from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.job import Job
from app.models.resume import Resume
from app.models.score import ATSScore
from app.services.scoring.ats_logic import score_resume
from sqlalchemy.future import select
import asyncio
from uuid import UUID

async def perform_scoring(job_id: UUID, resume_id: UUID):
    async with AsyncSessionLocal() as session:
        # Fetch Job and Resume
        job_result = await session.execute(select(Job).filter(Job.id == job_id))
        job = job_result.scalars().first()
        
        resume_result = await session.execute(select(Resume).filter(Resume.id == resume_id))
        resume = resume_result.scalars().first()
        
        if not job or not resume:
            return "Job or Resume not found"

        # Calculate Score
        # Calculate Score using new ATS Service
        from app.services.ats.scorer import calculate_ats_score
        
        # Concatenate title + description for better context
        job_text = f"{job.title}\n{job.description_text}"
        resume_text = resume.parsed_text or ""
        
        scores = calculate_ats_score(job_text, resume_text)
        
        # Save Score
        # Update ATSScore model fields if needed, for now mapping new outputs to existing schema
        # Dictionary support in JSONB columns is key here
        
        ats_score = ATSScore(
            resume_id=resume.id,
            job_id=job.id,
            overall_score=scores["overall_score"],
            keyword_score=scores["breakdown"]["keyword_match"],
            semantic_score=scores["breakdown"]["skill_match"], # Mapping "Skill Score" to "Semantic" column for now to avoid schema change
            matched_keywords=scores["matched_skills"], # Storing structured skills in keyword columns
            missing_keywords=scores["missing_skills"],
            insights=f"Match: {scores['overall_score']}%. Missing: {', '.join(scores['missing_skills'][:5])}"
        )
        session.add(ats_score)
        await session.commit()
        return f"Scored Job {job_id}: {scores['overall_score']}"

@celery_app.task
def score_job_task(job_id_str: str, resume_id_str: str):
    """
    Celery task to score a job against a resume.
    """
    import asyncio
    from uuid import UUID
    
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(perform_scoring(UUID(job_id_str), UUID(resume_id_str)))

async def perform_batch_scoring(resume_id: UUID):
    from sqlalchemy import delete
    from sqlalchemy.orm import selectinload
    
    async with AsyncSessionLocal() as session:
        # 1. Fetch Resume with Skills
        resume_result = await session.execute(
            select(Resume).options(selectinload(Resume.skills)).filter(Resume.id == resume_id)
        )
        resume = resume_result.scalars().first()
        if not resume:
            return "Resume not found"
            
        resume_skill_set = {s.skill_name.lower() for s in resume.skills}

        # 2. Fetch All Active Jobs with Skills
        # Eager load skills to avoid N+1 query problem
        jobs_result = await session.execute(
            select(Job).options(selectinload(Job.skills)).filter(Job.is_active == True)
        )
        jobs = jobs_result.scalars().all()
        
        if not jobs:
            return "No active jobs found"

        # 3. Clear existing scores for this resume (Fresh Analysis)
        await session.execute(delete(ATSScore).where(ATSScore.resume_id == resume_id))
        
        # 4. Score Each Job
        count = 0
        
        for job in jobs:
            job_skill_set = {s.skill_name.lower() for s in job.skills}
            
            # Simple Intersection Matching
            matched_skills = resume_skill_set.intersection(job_skill_set)
            missing_skills = job_skill_set - resume_skill_set
            
            # Calculate Score
            if not job_skill_set:
                # If job has no specific skills required, checking text match or default
                # For now, if no skills defined, we might give a base score or 0
                # Let's fallback to a text-based match if DB skills are empty (legacy jobs)
                 from app.services.ats.scorer import calculate_ats_score
                 job_text = f"{job.title}\n{job.description_text}"
                 resume_text = resume.parsed_text or ""
                 legacy_scores = calculate_ats_score(job_text, resume_text)
                 overall_score = legacy_scores["overall_score"]
                 final_matched = legacy_scores["matched_skills"]
                 final_missing = legacy_scores["missing_skills"]
                 kw_score = legacy_scores["breakdown"]["keyword_match"]
                 sem_score = legacy_scores["breakdown"]["skill_match"]
            else:
                match_count = len(matched_skills)
                total_required = len(job_skill_set)
                
                # Formula: (Matches / Total) * 100
                # weighted logic can be added later using skill.weight
                raw_score = (match_count / total_required) * 100
                overall_score = round(raw_score, 1)
                
                final_matched = list(matched_skills)
                final_missing = list(missing_skills)
                kw_score = overall_score # Simplified for now
                sem_score = overall_score # Simplified for now

            ats_score = ATSScore(
                resume_id=resume.id,
                job_id=job.id,
                overall_score=overall_score,
                keyword_score=kw_score,
                semantic_score=sem_score,
                matched_keywords=final_matched,
                missing_keywords=final_missing,
                insights=f"Match: {overall_score}%. Found: {len(final_matched)}/{len(job_skill_set) if job_skill_set else 'Text'} skills."
            )
            session.add(ats_score)
            count += 1
            
        await session.commit()
        return f"Batch Scored {count} jobs for Resume {resume_id}"

@celery_app.task
def score_all_jobs_task(resume_id_str: str):
    """
    Celery task to score ALL active jobs against a resume.
    """
    import asyncio
    from uuid import UUID
    
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(perform_batch_scoring(UUID(resume_id_str)))
