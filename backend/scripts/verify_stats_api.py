
import asyncio
import aiohttp
import sys

async def main():
    # Fetch latest resume ID
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.resume import Resume
        from sqlalchemy import select, desc
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Resume.id).order_by(desc(Resume.uploaded_at)).limit(1))
            resume_id = result.scalar()
            
        if not resume_id:
            print("❌ No resume found in DB.")
            return

        resume_id = str(resume_id)
        print(f"ℹ️ Testing with Resume ID: {resume_id}")

        url = f"http://localhost:8000/api/v1/scoring/stats/{resume_id}"
        print(f"Checking URL: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Body: {text}")
                
                # Simple validation
                if response.status == 200:
                    import json
                    data = json.loads(text)
                    if data['total_jobs_analyzed'] > 0:
                        print("✅ Stats API returned valid data.")
                        # Check insights for skill match evidence
                        if data['scores'] and 'matched_keywords' in data['scores'][0]:
                             print(f"✅ Top Match Skills: {data['scores'][0]['matched_keywords']}")
                    else:
                        print("⚠️ No jobs analyzed.")

    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
