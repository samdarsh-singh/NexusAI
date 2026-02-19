
from sqlalchemy import Column, String, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base_class import Base

class ResumeSkill(Base):
    __tablename__ = "resume_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    skill_name = Column(String, nullable=False, index=True)
    proficiency = Column(Float, default=1.0) # 0.0 to 1.0

    resume = relationship("Resume", back_populates="skills")

class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    skill_name = Column(String, nullable=False, index=True)
    weight = Column(Float, default=1.0) # Importance

    job = relationship("Job", back_populates="skills")
