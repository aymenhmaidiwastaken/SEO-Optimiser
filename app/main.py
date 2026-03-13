from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import init_db, get_db
from app.api.router import api_router
from app.models import CrawlJob, CrawlStatus
from app.export.html_report import render_html_report

base_dir = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(base_dir / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    (base_dir / "data").mkdir(exist_ok=True)
    await init_db()
    print(f"[SEO Optimizer] Ready at http://localhost:8080")
    yield


app = FastAPI(title="SEO Optimizer", lifespan=lifespan)

# API routes
app.include_router(api_router)


# ── Page routes ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CrawlJob).order_by(CrawlJob.created_at.desc()))
    jobs = result.scalars().all()
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs})


@app.get("/report/{job_id}", response_class=HTMLResponse)
async def report_page(request: Request, job_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import Page, Issue, Fix, CategoryScore
    job = await db.get(CrawlJob, job_id)
    if not job:
        return templates.TemplateResponse("index.html", {"request": request, "jobs": [], "error": "Not found"})

    pages = (await db.execute(select(Page).where(Page.crawl_job_id == job_id))).scalars().all()
    issues = (await db.execute(select(Issue).where(Issue.crawl_job_id == job_id))).scalars().all()
    fixes = (await db.execute(select(Fix).where(Fix.crawl_job_id == job_id))).scalars().all()
    scores = (await db.execute(select(CategoryScore).where(CategoryScore.crawl_job_id == job_id))).scalars().all()

    return templates.TemplateResponse("report.html", {
        "request": request, "job": job, "pages": pages,
        "issues": issues, "fixes": fixes, "scores": scores,
    })


@app.get("/export/{job_id}/html")
async def export_html(job_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import Page, Issue, Fix, CategoryScore
    job = await db.get(CrawlJob, job_id)
    pages = (await db.execute(select(Page).where(Page.crawl_job_id == job_id))).scalars().all()
    issues = (await db.execute(select(Issue).where(Issue.crawl_job_id == job_id))).scalars().all()
    fixes = (await db.execute(select(Fix).where(Fix.crawl_job_id == job_id))).scalars().all()
    scores = (await db.execute(select(CategoryScore).where(CategoryScore.crawl_job_id == job_id))).scalars().all()

    html = render_html_report({"job": job, "pages": pages, "issues": issues, "fixes": fixes, "scores": scores})
    return Response(content=html, media_type="text/html",
                   headers={"Content-Disposition": f"attachment; filename=seo-report-{job_id}.html"})


@app.get("/export/{job_id}/pdf")
async def export_pdf(job_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import Page, Issue, Fix, CategoryScore
    from app.export.pdf_report import generate_pdf_report

    job = await db.get(CrawlJob, job_id)
    pages = (await db.execute(select(Page).where(Page.crawl_job_id == job_id))).scalars().all()
    issues = (await db.execute(select(Issue).where(Issue.crawl_job_id == job_id))).scalars().all()
    fixes = (await db.execute(select(Fix).where(Fix.crawl_job_id == job_id))).scalars().all()
    scores = (await db.execute(select(CategoryScore).where(CategoryScore.crawl_job_id == job_id))).scalars().all()

    pdf = generate_pdf_report({"job": job, "pages": pages, "issues": issues, "fixes": fixes, "scores": scores})
    return Response(content=pdf, media_type="application/pdf",
                   headers={"Content-Disposition": f"attachment; filename=seo-report-{job_id}.pdf"})


# Static files mounted LAST
app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")
