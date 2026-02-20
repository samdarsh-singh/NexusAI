from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.api import deps
from app.models.score import ATSScore
from app.schemas.score import ATSScore as ATSScoreSchema
from app.workers.scoring import score_job_task

router = APIRouter()

@router.post("/score-job/{job_id}", status_code=202)
def trigger_scoring(
    job_id: str,
    resume_id: str = Body(..., embed=True),
):
    """
    Trigger scoring for a specific job and resume.
    """
    task = score_job_task.delay(job_id, resume_id)
    return {"message": "Scoring started", "task_id": str(task.id)}

@router.post("/analyze-resume/{resume_id}", status_code=202)
async def analyze_resume_against_market(
    resume_id: str,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Trigger scoring for a resume against ALL active jobs.
    """
    from app.models.job import Job
    
    # 1. Fetch all active jobs
    result = await db.execute(select(Job).filter(Job.is_active == True))
    jobs = result.scalars().all()
    
    if not jobs:
        raise HTTPException(status_code=404, detail="No active jobs found to analyze")

    # 2. Trigger Batch Celery Task
    # We use the new batch worker instead of iterating tasks
    from app.workers.scoring import score_all_jobs_task
    
    task = score_all_jobs_task.delay(resume_id)
        
    return {
        "message": "Market Analysis Started (Batch)", 
        "task_id": str(task.id)
    }

@router.get("/stats/{resume_id}")
async def get_ats_stats(
    resume_id: str,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Get aggregated ATS statistics for the dashboard.
    """
    from sqlalchemy import func
    try:
        resume_uuid = UUID(resume_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    # Aggregate Specs: count, avg score
    stats_query = select(
        func.count(ATSScore.id).label("total_jobs"),
        func.avg(ATSScore.overall_score).label("average_score")
    ).filter(ATSScore.resume_id == resume_uuid)
    
    result = await db.execute(stats_query)
    stats = result.one()
    
    # Get recent scores for list
    scores_result = await db.execute(
        select(ATSScore)
        .filter(ATSScore.resume_id == resume_uuid)
        .order_by(ATSScore.overall_score.desc())
        .limit(5)
    )
    top_scores = scores_result.scalars().all()
    
    return {
        "total_jobs_analyzed": stats.total_jobs or 0,
        "average_score": round(stats.average_score or 0, 1),
        "scores": top_scores 
    }

@router.get("/resume/{resume_id}")
async def get_scores_for_resume(
    resume_id: str,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Get all ATS scores for a specific resume, enriched with job title and company name.
    """
    from app.models.job import Job
    from app.models.company import Company

    try:
        resume_uuid = UUID(resume_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    result = await db.execute(
        select(ATSScore, Job.title.label("job_title"), Company.name.label("company_name"))
        .join(Job, ATSScore.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
        .filter(ATSScore.resume_id == resume_uuid)
        .order_by(ATSScore.overall_score.desc())
    )

    return [
        {
            "id": str(row.ATSScore.id),
            "job_id": str(row.ATSScore.job_id),
            "job_title": row.job_title,
            "company_name": row.company_name,
            "overall_score": row.ATSScore.overall_score,
            "keyword_score": row.ATSScore.keyword_score,
            "semantic_score": row.ATSScore.semantic_score,
            "matched_keywords": row.ATSScore.matched_keywords,
            "missing_keywords": row.ATSScore.missing_keywords,
            "insights": row.ATSScore.insights,
            "created_at": row.ATSScore.created_at.isoformat() if row.ATSScore.created_at else None,
        }
        for row in result.all()
    ]

@router.get("/results/{job_id}", response_model=List[ATSScoreSchema])
async def get_scores_for_job(
    job_id: str,
    db: AsyncSession = Depends(deps.get_db)
):
    try:
        job_uuid = UUID(job_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    result = await db.execute(select(ATSScore).filter(ATSScore.job_id == job_uuid))
    return result.scalars().all()
