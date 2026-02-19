from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    parsed_text = Column(Text, nullable=True)
    skills_extracted = Column(JSONB, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="UPLOADED", nullable=False) # UPLOADED, PARSING, PARSED, FAILED
    error_reason = Column(Text, nullable=True)

    ats_scores = relationship("ATSScore", back_populates="resume")
    skills = relationship("ResumeSkill", back_populates="resume", cascade="all, delete-orphan")
