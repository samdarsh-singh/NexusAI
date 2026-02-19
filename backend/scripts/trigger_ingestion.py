
import asyncio
import aiohttp
import sys

# Trigger Ingestion
# We'll call the internal function directly via a script to avoid setting up API trigger if it doesn't exist yet, 
# or use Celery directly. But easier to use API if available.
# Checking task.md, user said "Job Ingestion Service" is done.
# But I am not sure if there is an HTTP endpoint for it.
# Let's try to invoke via Celery through python shell or just run the standalone scraper test.

# To be robust, I will create a script that connects to Celery and sends the task.
from celery import Celery

app = Celery('worker', broker='redis://localhost:6379/0')

def trigger_ingestion():
    print("Triggering Ingestion Task...")
    # Matches app.workers.ingestion.fetch_jobs_task
    # Note: Using send_task is safer if we don't have the code imported here
    res = app.send_task("app.workers.ingestion.fetch_jobs_task", args=["Software Engineer", "Dubai"])
    print(f"Task Sent: {res.id}")

if __name__ == "__main__":
    trigger_ingestion()
