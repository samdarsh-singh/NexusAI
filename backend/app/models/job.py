from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, index=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("job_sources.id"), nullable=False)
    external_id = Column(String, index=True, nullable=True) # ID from the source system
    location = Column(String, nullable=True)
    description_text = Column(Text, nullable=True)
    
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    currency = Column(String, default="USD")
    
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Hash for deduplication (title + company + location)
    job_hash = Column(String, unique=True, index=True, nullable=False)

    company = relationship("Company", back_populates="jobs")
    source = relationship("JobSource", back_populates="jobs")
    ats_scores = relationship("ATSScore", back_populates="job")
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
