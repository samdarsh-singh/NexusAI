from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta

from app.api import deps
from app.models.job import Job
from app.models.resume import Resume
from app.models.score import ATSScore

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(deps.get_db)):
    # 1. Total Jobs
    total_jobs_result = await db.execute(select(func.count(Job.id)))
    total_jobs = total_jobs_result.scalar() or 0
    
    # 2. Total Resumes
    total_resumes_result = await db.execute(select(func.count(Resume.id)))
    total_resumes = total_resumes_result.scalar() or 0
    
    # 3. Average ATS Score
    avg_score_result = await db.execute(select(func.avg(ATSScore.overall_score)))
    average_ats_score = avg_score_result.scalar() or 0.0
    
    return {
        "total_jobs": total_jobs,
        "total_resumes": total_resumes,
        "average_ats_score": round(average_ats_score, 1),
        "active_scrapers": 4  # Placeholder
    }

@router.get("/ats-trend")
async def get_ats_trend(db: AsyncSession = Depends(deps.get_db)):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    query = (
        select(
            func.date_trunc('day', ATSScore.created_at).label("day"),
            func.avg(ATSScore.overall_score).label("avg_score")
        )
        .filter(ATSScore.created_at >= thirty_days_ago)
        .group_by("day")
        .order_by("day")
    )
    result = await db.execute(query)
    
    data = []
    for row in result.all():
        date_str = row.day.strftime("%b %d") if row.day else "Unknown"
        data.append({
            "date": date_str,
            "score": round(row.avg_score, 1) if row.avg_score else 0
        })
    
    return data
