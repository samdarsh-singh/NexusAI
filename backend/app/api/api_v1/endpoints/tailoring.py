from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import io

from app.api import deps
from app.models.tailored_resume import TailoredResume
from app.models.resume import Resume
from app.models.job import Job
from app.models.company import Company

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /resumes/{resume_id}/tailor/{job_id}
# ---------------------------------------------------------------------------

@router.post("/{resume_id}/tailor/{job_id}", status_code=202)
async def tailor_resume(
    resume_id: str,
    job_id: str,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Trigger async tailoring of a resume for a specific job.
    Returns 202 with tailored_resume_id and PENDING status.
    Idempotent: returns existing PENDING/DRAFT record if one already exists.
    """
    try:
        resume_uuid = UUID(resume_id)
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Validate resume exists and is PARSED
    res_result = await db.execute(select(Resume).filter(Resume.id == resume_uuid))
    resume = res_result.scalars().first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.status != "PARSED":
        raise HTTPException(status_code=422, detail=f"Resume status is '{resume.status}'; must be PARSED")

    # Validate job exists
    job_result = await db.execute(select(Job).filter(Job.id == job_uuid))
    job = job_result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Idempotency: return existing non-FAILED record for same resume+job
    existing_result = await db.execute(
        select(TailoredResume)
        .filter(TailoredResume.resume_id == resume_uuid)
        .filter(TailoredResume.job_id == job_uuid)
        .filter(TailoredResume.status.in_(["PENDING", "DRAFT", "APPROVED", "DOWNLOADED"]))
        .order_by(TailoredResume.created_at.desc())
        .limit(1)
    )
    existing = existing_result.scalars().first()
    if existing:
        return {"tailored_resume_id": str(existing.id), "status": existing.status}

    # Create new TailoredResume record
    tailored = TailoredResume(
        resume_id=resume_uuid,
        job_id=job_uuid,
        original_text=resume.parsed_text or "",
        status="PENDING",
    )
    db.add(tailored)
    await db.commit()
    await db.refresh(tailored)

    # Dispatch Celery task
    from app.workers.tailoring import tailor_resume_task
    tailor_resume_task.delay(str(tailored.id))

    return {"tailored_resume_id": str(tailored.id), "status": "PENDING"}


# ---------------------------------------------------------------------------
# GET /resumes/tailored  (list all)
# ---------------------------------------------------------------------------

@router.get("/tailored")
async def list_tailored_resumes(
    db: AsyncSession = Depends(deps.get_db),
):
    """
    List all tailored resumes ordered by most recent first.
    Joins with Job and Company to include display metadata.
    """
    result = await db.execute(
        select(TailoredResume, Job, Company)
        .join(Job, TailoredResume.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
        .order_by(TailoredResume.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": str(t.id),
            "resume_id": str(t.resume_id),
            "job_id": str(t.job_id),
            "job_title": j.title,
            "company_name": c.name,
            "status": t.status,
            "ats_score_before": t.ats_score_before,
            "ats_score_after": t.ats_score_after,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t, j, c in rows
    ]


# ---------------------------------------------------------------------------
# GET /resumes/tailored/{id}
# ---------------------------------------------------------------------------

@router.get("/tailored/{tailored_id}")
async def get_tailored_resume(
    tailored_id: str,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Poll for tailored resume status and data.
    Returns full record including change_summary, ATS scores, and job info.
    """
    try:
        tailored_uuid = UUID(tailored_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(TailoredResume).filter(TailoredResume.id == tailored_uuid)
    )
    tailored = result.scalars().first()
    if not tailored:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    # Join job → company for title/company display
    job_result = await db.execute(
        select(Job, Company)
        .join(Company, Job.company_id == Company.id)
        .filter(Job.id == tailored.job_id)
    )
    job_row = job_result.first()
    job_title = job_row[0].title if job_row else None
    company_name = job_row[1].name if job_row else None

    return {
        "id": str(tailored.id),
        "resume_id": str(tailored.resume_id),
        "job_id": str(tailored.job_id),
        "job_title": job_title,
        "company_name": company_name,
        "status": tailored.status,
        "original_text": tailored.original_text,
        "tailored_text": tailored.tailored_text,
        "change_summary": tailored.change_summary,
        "ats_score_before": tailored.ats_score_before,
        "ats_score_after": tailored.ats_score_after,
        "error_message": tailored.error_message,
        "created_at": tailored.created_at.isoformat() if tailored.created_at else None,
    }


# ---------------------------------------------------------------------------
# POST /resumes/tailored/{id}/approve
# ---------------------------------------------------------------------------

@router.post("/tailored/{tailored_id}/approve")
async def approve_tailored_resume(
    tailored_id: str,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Approve a DRAFT tailored resume. Sets status to APPROVED.
    """
    try:
        tailored_uuid = UUID(tailored_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(TailoredResume).filter(TailoredResume.id == tailored_uuid)
    )
    tailored = result.scalars().first()
    if not tailored:
        raise HTTPException(status_code=404, detail="Tailored resume not found")
    if tailored.status != "DRAFT":
        raise HTTPException(
            status_code=422,
            detail=f"Cannot approve: current status is '{tailored.status}' (expected DRAFT)",
        )

    tailored.status = "APPROVED"
    await db.commit()

    return {"id": str(tailored.id), "status": "APPROVED"}


# ---------------------------------------------------------------------------
# GET /resumes/tailored/{id}/download
# ---------------------------------------------------------------------------

@router.get("/tailored/{tailored_id}/download")
async def download_tailored_resume(
    tailored_id: str,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Download the tailored resume as a PDF.
    Requires status=APPROVED. Sets status to DOWNLOADED on first download.
    """
    try:
        tailored_uuid = UUID(tailored_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(TailoredResume).filter(TailoredResume.id == tailored_uuid)
    )
    tailored = result.scalars().first()
    if not tailored:
        raise HTTPException(status_code=404, detail="Tailored resume not found")
    if tailored.status not in ("APPROVED", "DOWNLOADED"):
        raise HTTPException(
            status_code=403,
            detail=f"Resume must be APPROVED before downloading (current: '{tailored.status}')",
        )

    # Get candidate name for PDF metadata
    resume_result = await db.execute(
        select(Resume).filter(Resume.id == tailored.resume_id)
    )
    resume = resume_result.scalars().first()
    candidate_name = resume.candidate_name if resume else ""

    # Generate PDF
    from app.services.tailoring.pdf_generator import generate_pdf
    pdf_bytes = generate_pdf(tailored.tailored_text or "", candidate_name=candidate_name)

    # Mark as DOWNLOADED
    if tailored.status == "APPROVED":
        tailored.status = "DOWNLOADED"
        await db.commit()

    filename = f"tailored_resume_{tailored_id[:8]}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
