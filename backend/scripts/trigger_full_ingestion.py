
from celery import Celery

app = Celery('worker', broker='redis://redis:6379/0')

def trigger_full_ingestion():
    print("Triggering Full Dataset Ingestion (*)...")
    res = app.send_task("app.workers.ingestion.fetch_jobs_task", args=["*", "Dubai"])
    print(f"Task Sent: {res.id}")

if __name__ == "__main__":
    trigger_full_ingestion()
