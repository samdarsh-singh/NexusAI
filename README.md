
# NexusAI - Intelligent Job Aggregator & ATS Platform

**NexusAI** is an advanced **Intelligent Job Aggregator & ATS Scoring Engine** designed to bridge the gap between talent and opportunity.

By leveraging **AI-driven Resume Parsing (NLP)** and **Real-time Job Market Analysis**, NexusAI provides candidates with:
- **Smart Job Aggregation**: Centralized access to tech jobs from multiple sources.
- **Deep ATS Scoring**: Batch-processing of resumes against hundreds of jobs to find the perfect semantic match.
- **Skill Gap Analysis**: Actionable insights on missing keywords and skills.
- **Instant Feedback**: Real-time scoring pipeline powered by Celery & Redis.

## Project Structure

- **`backend/`**: FastAPI application source code and configs.
- **`frontend/`**: Next.js application source code.
- **`data/`**: External data storage (mounted volume).
- **`venv/`**: Python virtual environment (if running locally).
- **`docker-compose.yml`**: Orchestration.

## Prerequisites

- Docker & Docker Compose (or Podman)
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

## quick Start (Docker)

1. **Build and Run**:
   ```bash
   docker-compose up --build
   ```
   This will start:
   - Backend API: http://localhost:8000
   - Frontend UI: http://localhost:3000
   - PostgreSQL, MongoDB, Redis, and Celery Workers.

2. **Access Documentation**:
   - API Docs: http://localhost:8000/docs
   - Dashboard: http://localhost:3000

## Manual Setup (Local Development)

### Backend
1. Navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run migrations and start server:
   ```bash
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

### Frontend
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start development server:
   ```bash
   npm run dev
   ```

## Key Features
- **Job Aggregation**: Scrapes and normalizes jobs from multiple sources.
- **Resume Parsing**: Extracts text and skills from PDFs.
- **ATS Scoring**: Batch scores jobs against your resume with detailed breakdown.
- **Dashboard**: Visualizes application tracking and market fit.
