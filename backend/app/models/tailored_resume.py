from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class TailoredResume(Base):
    __tablename__ = "tailored_resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    tailored_text = Column(Text, nullable=True)   # null while PENDING
    change_summary = Column(JSONB, nullable=True)  # list[ResumeDiff]
    ats_score_before = Column(Float, nullable=True)
    ats_score_after = Column(Float, nullable=True)
    status = Column(String, default="PENDING", nullable=False)
    # Status flow: PENDING → DRAFT → APPROVED → DOWNLOADED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="tailored_resumes")
    job = relationship("Job", back_populates="tailored_resumes")

    __table_args__ = (
        Index("ix_tailored_resumes_resume_id", "resume_id"),
        Index("ix_tailored_resumes_job_id", "job_id"),
    )
