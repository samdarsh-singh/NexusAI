from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.tailored_resume import TailoredResume
from app.models.resume import Resume
from app.models.job import Job
from app.models.score import ATSScore
from sqlalchemy.future import select
import asyncio
from uuid import UUID


async def perform_tailoring(tailored_resume_id: UUID):
    async with AsyncSessionLocal() as session:
        # 1. Load TailoredResume record
        result = await session.execute(
            select(TailoredResume).filter(TailoredResume.id == tailored_resume_id)
        )
        tailored = result.scalars().first()
        if not tailored:
            return f"TailoredResume {tailored_resume_id} not found"

        # 2. Load Resume and Job
        resume_result = await session.execute(
            select(Resume).filter(Resume.id == tailored.resume_id)
        )
        resume = resume_result.scalars().first()

        job_result = await session.execute(
            select(Job).filter(Job.id == tailored.job_id)
        )
        job = job_result.scalars().first()

        if not resume or not job:
            tailored.status = "FAILED"
            tailored.error_message = "Resume or Job not found"
            await session.commit()
            return "Resume or Job not found"

        # 3. Load existing ATSScore for this resume+job
        score_result = await session.execute(
            select(ATSScore)
            .filter(ATSScore.resume_id == tailored.resume_id)
            .filter(ATSScore.job_id == tailored.job_id)
            .order_by(ATSScore.created_at.desc())
            .limit(1)
        )
        ats_score = score_result.scalars().first()

        if not ats_score:
            # No existing score — run scoring inline
            from app.services.ats.scorer import calculate_ats_score
            job_text = f"{job.title}\n{job.description_text or ''}"
            score_data = calculate_ats_score(job_text, resume.parsed_text or "")
            missing_skills = score_data["missing_skills"]
            matched_skills = score_data["matched_skills"]
            ats_before = score_data["overall_score"]
        else:
            missing_skills = ats_score.missing_keywords or []
            matched_skills = ats_score.matched_keywords or []
            ats_before = ats_score.overall_score

        try:
            # 4. Run tailoring engine
            from app.services.tailoring.engine import tailor_resume
            job_text = f"{job.title}\n{job.description_text or ''}"

            result_data = tailor_resume(
                resume_text=tailored.original_text,
                job_text=job_text,
                missing_skills=missing_skills,
                matched_skills=matched_skills,
                ats_score_before=ats_before,
            )

            # 5. Persist results
            tailored.tailored_text = result_data["tailored_text"]
            tailored.change_summary = result_data["change_summary"]
            tailored.ats_score_before = result_data["ats_score_before"]
            tailored.ats_score_after = result_data["ats_score_after"]
            tailored.status = "DRAFT"
            await session.commit()

            return (
                f"Tailored resume {tailored_resume_id}: "
                f"ATS {result_data['ats_score_before']} → {result_data['ats_score_after']}"
            )

        except Exception as e:
            tailored.status = "FAILED"
            tailored.error_message = str(e)
            tailored.change_summary = [
                {
                    "section_name": "Error",
                    "before_text": "",
                    "after_text": "",
                    "reason": f"Tailoring failed: {str(e)}",
                    "injected": False,
                    "skill": "",
                }
            ]
            await session.commit()
            return f"Failed: {str(e)}"


@celery_app.task
def tailor_resume_task(tailored_resume_id_str: str):
    """
    Celery task: generate tailored resume from PENDING → DRAFT.
    """
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(perform_tailoring(UUID(tailored_resume_id_str)))
