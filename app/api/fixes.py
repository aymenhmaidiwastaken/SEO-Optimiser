from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Fix
from app.schemas import FixResponse

router = APIRouter(prefix="/api/fixes", tags=["fixes"])


@router.get("/{job_id}/sitemap")
async def download_sitemap(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Fix).where(Fix.crawl_job_id == job_id, Fix.fix_type == "sitemap")
    )
    fix = result.scalars().first()
    if not fix:
        raise HTTPException(status_code=404, detail="No sitemap fix found")
    return PlainTextResponse(fix.suggested, media_type="application/xml",
                            headers={"Content-Disposition": "attachment; filename=sitemap.xml"})


@router.get("/{job_id}/robots")
async def download_robots(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Fix).where(Fix.crawl_job_id == job_id, Fix.fix_type == "robots_txt")
    )
    fix = result.scalars().first()
    if not fix:
        raise HTTPException(status_code=404, detail="No robots.txt fix found")
    return PlainTextResponse(fix.suggested, media_type="text/plain",
                            headers={"Content-Disposition": "attachment; filename=robots.txt"})
