from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class ATSScoreBase(BaseModel):
    overall_score: float
    keyword_score: float
    semantic_score: float
    insights: Optional[str] = None
    missing_keywords: Optional[Any] = None
    matched_keywords: Optional[Any] = None

class ATSScoreCreate(ATSScoreBase):
    resume_id: UUID
    job_id: UUID

class ATSScore(ATSScoreBase):
    id: UUID
    resume_id: UUID
    job_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
