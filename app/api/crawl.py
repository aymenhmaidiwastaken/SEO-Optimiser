import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, async_session
from app.models import CrawlJob, CrawlStatus
from app.schemas import CrawlRequest, CrawlJobResponse
from app.crawler.engine import run_crawl

router = APIRouter(prefix="/api/crawl", tags=["crawl"])


@router.post("/", response_model=CrawlJobResponse)
async def start_crawl(req: CrawlRequest, db: AsyncSession = Depends(get_db)):
    job = CrawlJob(
        url=req.url,
        max_pages=req.max_pages,
        max_depth=req.max_depth,
        status=CrawlStatus.CRAWLING,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Run crawl in background
    asyncio.create_task(safe_crawl(job.id, req.url, req.max_pages, req.max_depth))

    return job


async def safe_crawl(job_id: int, url: str, max_pages: int, max_depth: int):
    try:
        await run_crawl(job_id, async_session, url, max_pages, max_depth)
    except Exception as e:
        async with async_session() as db:
            job = await db.get(CrawlJob, job_id)
            if job:
                job.status = CrawlStatus.FAILED
                job.error_message = str(e)
                await db.commit()


@router.get("/", response_model=list[CrawlJobResponse])
async def list_crawls(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CrawlJob).order_by(CrawlJob.created_at.desc()))
    return result.scalars().all()


@router.get("/{job_id}", response_model=CrawlJobResponse)
async def get_crawl(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(CrawlJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return job


@router.delete("/{job_id}")
async def delete_crawl(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(CrawlJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    await db.delete(job)
    await db.commit()
    return {"ok": True}
