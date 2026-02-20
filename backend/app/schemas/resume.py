from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class ResumeBase(BaseModel):
    candidate_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None

class ResumeCreate(ResumeBase):
    pass

class ResumeInDBBase(ResumeBase):
    id: UUID
    candidate_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    file_path: str
    parsed_text: Optional[str] = None
    skills_extracted: Optional[Any] = None  # stored as list[str] by parser, dict by legacy code
    uploaded_at: datetime
    status: str
    error_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class Resume(ResumeInDBBase):
    pass
