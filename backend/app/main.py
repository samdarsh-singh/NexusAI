from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.mongodb import mongo_db
from app.api.api_v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    mongo_db.connect()
    yield
    # Shutdown
    mongo_db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
def root():
    return {"message": "NexusAI API is running"}

from fastapi.staticfiles import StaticFiles
import os

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="uploads"), name="static")

app.include_router(api_router, prefix=settings.API_V1_STR)
