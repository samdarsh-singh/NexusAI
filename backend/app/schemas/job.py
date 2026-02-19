from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Shared properties
class JobBase(BaseModel):
    title: str
    location: Optional[str] = None
    description_text: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = "USD"
    external_id: Optional[str] = None

# Properties to receive on item creation
class JobCreate(JobBase):
    company_name: str
    company_domain: Optional[str] = None
    company_logo_url: Optional[str] = None
    source_name: str
    source_url: Optional[str] = None
    posted_at: Optional[datetime] = None

# Properties shared by models stored in DB
class JobInDBBase(JobBase):
    id: UUID
    company_id: UUID
    source_id: int
    created_at: datetime
    is_active: bool
    job_hash: str

    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class Job(JobInDBBase):
    pass
