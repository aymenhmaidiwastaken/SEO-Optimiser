from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import CrawlJob, Page, Issue, Fix, CategoryScore
from app.schemas import (
    ReportResponse, CrawlJobResponse, PageResponse,
    IssueResponse, FixResponse, CategoryScoreResponse,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{job_id}", response_model=ReportResponse)
async def get_report(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(CrawlJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Crawl job not found")

    pages = (await db.execute(select(Page).where(Page.crawl_job_id == job_id))).scalars().all()
    issues = (await db.execute(select(Issue).where(Issue.crawl_job_id == job_id))).scalars().all()
    fixes = (await db.execute(select(Fix).where(Fix.crawl_job_id == job_id))).scalars().all()
    scores = (await db.execute(select(CategoryScore).where(CategoryScore.crawl_job_id == job_id))).scalars().all()

    return ReportResponse(
        job=CrawlJobResponse.model_validate(job),
        scores=[CategoryScoreResponse.model_validate(s) for s in scores],
        issues=[IssueResponse.model_validate(i) for i in issues],
        fixes=[FixResponse.model_validate(f) for f in fixes],
        pages=[PageResponse.model_validate(p) for p in pages],
    )


@router.get("/{job_id}/issues", response_model=list[IssueResponse])
async def get_issues(
    job_id: int,
    category: str | None = None,
    severity: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Issue).where(Issue.crawl_job_id == job_id)
    if category:
        query = query.where(Issue.category == category)
    if severity:
        query = query.where(Issue.severity == severity)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{job_id}/pages", response_model=list[PageResponse])
async def get_pages(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Page).where(Page.crawl_job_id == job_id))
    return result.scalars().all()


@router.get("/{job_id}/fixes", response_model=list[FixResponse])
async def get_fixes(
    job_id: int,
    fix_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Fix).where(Fix.crawl_job_id == job_id)
    if fix_type:
        query = query.where(Fix.fix_type == fix_type)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{job_id}/scores", response_model=list[CategoryScoreResponse])
async def get_scores(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CategoryScore).where(CategoryScore.crawl_job_id == job_id))
    return result.scalars().all()
