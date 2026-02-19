
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.skills import JobSkill
from sqlalchemy import func, select

async def check_skills():
    async with AsyncSessionLocal() as session:
        count = await session.execute(select(func.count(JobSkill.id)))
        print(f"Total Job Skills: {count.scalar()}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_skills())
