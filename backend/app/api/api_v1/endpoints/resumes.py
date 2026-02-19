from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import shutil
import os
from uuid import uuid4
import pdfminer.high_level

from app.api import deps
from app.models.resume import Resume
from app.schemas.resume import Resume as ResumeSchema

router = APIRouter()

UPLOAD_DIR = "uploads/resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def extract_text_from_pdf(file_path: str) -> str:
    try:
        text = pdfminer.high_level.extract_text(file_path)
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

@router.post("/", response_model=ResumeSchema)
async def upload_resume(
    candidate_name: str = Form(...),
    email: str = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Upload a resume (PDF) and parse it.
    """
    file_id = str(uuid4())
    ext = file.filename.split('.')[-1]
    file_path = f"{UPLOAD_DIR}/{file_id}.{ext}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    resume = Resume(
        candidate_name=candidate_name,
        email=email,
        file_path=file_path,
        parsed_text=None,
        skills_extracted={},
        status="UPLOADED"
    )
    
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    
    # Trigger Async Parsing
    from app.workers.parsing import parse_resume_task
    parse_resume_task.delay(str(resume.id))
    
    return resume

@router.get("/{resume_id}", response_model=ResumeSchema)
async def get_resume(
    resume_id: str,
    db: AsyncSession = Depends(deps.get_db)
):
    from uuid import UUID
    try:
        resume_uuid = UUID(resume_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    result = await db.execute(select(Resume).filter(Resume.id == resume_uuid))
    resume = result.scalars().first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
