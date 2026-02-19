
import asyncio
import aiohttp
import os
import sys
from uuid import uuid4

API_URL = "http://localhost:8000/api/v1"
TEST_PDF_PATH = "data/samdarsh-resume-ai.pdf"
INVALID_PDF_PATH = "data/invalid.pdf"

# Ensure test data exists
if not os.path.exists(TEST_PDF_PATH):
    print(f"❌ Test file missing: {TEST_PDF_PATH}")
    sys.exit(1)

with open(INVALID_PDF_PATH, "w") as f:
    f.write("This is not a PDF")

async def test_server_health():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_URL}/jobs/") as resp:
                if resp.status == 200:
                    print("✅ Backend is UP")
                    return True
                else:
                    print(f"❌ Backend returned {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Backend unreachable: {e}")
            return False

async def test_resume_upload(session, file_path, name, expect_fail=False):
    data = aiohttp.FormData()
    data.add_field('candidate_name', name)
    data.add_field('file',
                   open(file_path, 'rb'),
                   filename=os.path.basename(file_path),
                   content_type='application/pdf')

    async with session.post(f"{API_URL}/resumes/", data=data) as resp:
        if resp.status != 200:
            print(f"❌ Upload failed for {name}: {resp.status}")
            return None
        
        result = await resp.json()
        resume_id = result['id']
        print(f"   Upload accepted. ID: {resume_id} (Status: {result['status']})")
        
        # Poll for completion
        for _ in range(10):
            await asyncio.sleep(1)
            async with session.get(f"{API_URL}/resumes/{resume_id}") as r:
                res = await r.json()
                status = res['status']
                if status in ['PARSED', 'FAILED']:
                    if expect_fail and status == 'FAILED':
                        print(f"✅ {name} reached FAILED state as expected. Reason: {res.get('error_reason')}")
                        return resume_id
                    elif not expect_fail and status == 'PARSED':
                        print(f"✅ {name} reached PARSED state successfully.")
                        
                        # Verify Extraction
                        print(f"   - Name: {res.get('candidate_name')}")
                        print(f"   - Email: {res.get('email')}")
                        print(f"   - Phone: {res.get('phone')}")
                        
                        if res.get('candidate_name') == "Candidate":
                             print("⚠️ Warning: Name was not extracted (remained default).")
                        
                        return resume_id
                    else:
                        print(f"❌ {name} ended in unexpected state: {status} (Expected: {'FAILED' if expect_fail else 'PARSED'})")
                        return None
        
        print(f"❌ {name} timed out in state: {status}")
        return None

async def test_scoring(session, resume_id):
    print(f"   Triggering scoring for {resume_id}...")
    async with session.post(f"{API_URL}/scoring/analyze-resume/{resume_id}") as resp:
        if resp.status not in [200, 202]:
            print(f"❌ Scoring trigger failed: {resp.status}")
            return False
            
    # Wait for scores
    await asyncio.sleep(3)
    
    async with session.get(f"{API_URL}/scoring/resume/{resume_id}") as resp:
        scores = await resp.json()
        if isinstance(scores, list) and len(scores) > 0:
             avg_score = sum(s.get('overall_score', 0) for s in scores) / len(scores)
             print(f"✅ Scoring successful. Jobs Analyzed: {len(scores)}, Avg Score: {avg_score:.2f}")
             return True
        else:
             print(f"⚠️ Scoring triggered but no results found (Make sure jobs exist in DB). Response: {scores}")
             return False

async def main():
    print("🚀 Starting Self-Test...")
    
    if not await test_server_health():
        sys.exit(1)
        
    async with aiohttp.ClientSession() as session:
        # 1. Valid Upload
        print("\n1️⃣ Testing Valid Resume Upload...")
        valid_id = await test_resume_upload(session, TEST_PDF_PATH, "Valid User")
        
        # 2. Invalid Upload
        print("\n2️⃣ Testing Invalid Resume Upload...")
        await test_resume_upload(session, INVALID_PDF_PATH, "Invalid User", expect_fail=True)
        
        # 3. Scoring
        if valid_id:
            print("\n3️⃣ Testing ATS Scoring...")
            await test_scoring(session, valid_id)
            
    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    asyncio.run(main())
