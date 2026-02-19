from sqlalchemy import Column, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base

class ATSScore(Base):
    __tablename__ = "ats_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    
    overall_score = Column(Float, nullable=False)
    keyword_score = Column(Float, nullable=False)
    semantic_score = Column(Float, nullable=False)
    
    missing_keywords = Column(JSONB, nullable=True)
    matched_keywords = Column(JSONB, nullable=True)
    insights = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="ats_scores")
    job = relationship("Job", back_populates="ats_scores")
