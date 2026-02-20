import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from uuid import UUID

from app.api import deps
from app.models.job import Job
from app.models.company import Company
from app.models.job_source import JobSource

router = APIRouter()
logger = logging.getLogger(__name__)


def _row_to_dict(row) -> dict:
    """Convert a joined Job/Company/JobSource row to a plain dict."""
    job = row.Job
    return {
        "id": str(job.id),
        "title": job.title,
        "company_name": row.company_name,
        "source_name": row.source_name,
        "location": job.location,
        "description_text": job.description_text,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "currency": job.currency,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "is_active": job.is_active,
    }


@router.post("/ingest", status_code=202)
def trigger_ingestion(query: str, location: str):
    """Trigger background job ingestion."""
    from app.workers.ingestion import fetch_jobs_task
    task = fetch_jobs_task.delay(query, location)
    return {"message": "Ingestion started", "task_id": str(task.id)}


@router.get("/")
async def list_jobs(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
):
    """List jobs with company name and source name joined."""
    stmt = (
        select(
            Job,
            Company.name.label("company_name"),
            JobSource.name.label("source_name"),
        )
        .join(Company, Job.company_id == Company.id)
        .join(JobSource, Job.source_id == JobSource.id)
        .offset(skip)
        .limit(limit)
    )
    if search:
        stmt = stmt.filter(Job.title.ilike(f"%{search}%"))

    result = await db.execute(stmt)
    rows = result.all()
    logger.info(f"GET /jobs — returned {len(rows)} rows (skip={skip}, limit={limit})")
    return [_row_to_dict(row) for row in rows]


@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(deps.get_db)):
    """Get a single job by UUID, with company name and source name joined."""
    logger.info(f"GET /jobs/{job_id} — incoming request")

    try:
        job_uuid = UUID(job_id)
    except ValueError:
        logger.warning(f"GET /jobs/{job_id} — invalid UUID format")
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    stmt = (
        select(
            Job,
            Company.name.label("company_name"),
            JobSource.name.label("source_name"),
        )
        .join(Company, Job.company_id == Company.id)
        .join(JobSource, Job.source_id == JobSource.id)
        .filter(Job.id == job_uuid)
    )

    result = await db.execute(stmt)
    row = result.first()

    if not row:
        logger.warning(f"GET /jobs/{job_id} — not found in DB")
        raise HTTPException(status_code=404, detail="Job not found")

    logger.info(f"GET /jobs/{job_id} — found: '{row.Job.title}' @ '{row.company_name}'")
    return _row_to_dict(row)
