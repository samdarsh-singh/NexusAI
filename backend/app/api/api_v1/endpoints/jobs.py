from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.api import deps
from app.models.job import Job
from app.schemas.job import Job as JobSchema
from app.workers.ingestion import fetch_jobs_task

router = APIRouter()

@router.post("/ingest", status_code=202)
def trigger_ingestion(
    query: str,
    location: str,
):
    """
    Trigger background job ingestion.
    """
    task = fetch_jobs_task.delay(query, location)
    return {"message": "Ingestion started", "task_id": str(task.id)}

@router.get("/", response_model=List[JobSchema])
async def list_jobs(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """
    List jobs with optional search filter.
    """
    query = select(Job).offset(skip).limit(limit)
    if search:
        query = query.filter(Job.title.ilike(f"%{search}%"))
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{job_id}", response_model=JobSchema)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Get job by ID.
    """
    from uuid import UUID
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(select(Job).filter(Job.id == job_uuid))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
