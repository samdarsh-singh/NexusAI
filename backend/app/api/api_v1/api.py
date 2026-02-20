from fastapi import APIRouter
from app.api.api_v1.endpoints import jobs, resumes, scoring, dashboard, tailoring

api_router = APIRouter()
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(tailoring.router, prefix="/resumes", tags=["tailoring"])
api_router.include_router(scoring.router, prefix="/scoring", tags=["scoring"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
