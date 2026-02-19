from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # linkedin, indeed, naukri
    base_url = Column(String, nullable=True)

    jobs = relationship("Job", back_populates="source")
