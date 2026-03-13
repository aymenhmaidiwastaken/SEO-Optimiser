import asyncio
import aiohttp
import datetime
from collections import deque
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import CrawlJob, Page, CrawlStatus
from app.crawler.fetcher import fetch_url
from app.crawler.parser import parse_html, ParsedPage
from app.crawler.robots import AsyncRobotsChecker
from app.crawler.sitemap import discover_sitemap_urls
from app.crawler.url_utils import normalize_url, is_same_domain

# Global dict for SSE progress
crawl_progress: dict[int, dict] = {}


async def run_crawl(job_id: int, session_factory, url: str, max_pages: int, max_depth: int):
    progress = {
        "status": "starting",
        "pages_crawled": 0,
        "pages_found": 0,
        "current_url": "",
        "errors": [],
    }
    crawl_progress[job_id] = progress

    parsed_pages: list[ParsedPage] = []
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque()  # (url, depth)

    base_url = normalize_url(url) or url
    queue.append((base_url, 0))

    connector = aiohttp.TCPConnector(limit=settings.MAX_CONCURRENT_REQUESTS, ssl=False)
    async with aiohttp.ClientSession(
        connector=connector,
        headers={"User-Agent": settings.USER_AGENT},
    ) as http_session:
        # Fetch robots.txt
        robots = AsyncRobotsChecker()
        await robots.fetch_robots(http_session, base_url)

        # Discover sitemap URLs
        sitemap_refs = robots.get_sitemaps(base_url)
        sitemap_urls = await discover_sitemap_urls(http_session, base_url, sitemap_refs or None)
        for surl in sitemap_urls:
            norm = normalize_url(surl)
            if norm and is_same_domain(norm, base_url) and norm not in visited:
                queue.append((norm, 1))

        progress["status"] = "crawling"
        progress["pages_found"] = len(queue)

        sem = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)

        async def crawl_url(crawl_url_str: str, depth: int):
            async with sem:
                if crawl_url_str in visited:
                    return
                if len(visited) >= max_pages:
                    return
                if not robots.can_fetch(crawl_url_str, settings.USER_AGENT):
                    return

                visited.add(crawl_url_str)
                progress["current_url"] = crawl_url_str

                result = await fetch_url(http_session, crawl_url_str)

                if result.error:
                    progress["errors"].append({"url": crawl_url_str, "error": result.error})
                    return

                # Store page in DB
                async with session_factory() as db:
                    page = Page(
                        crawl_job_id=job_id,
                        url=crawl_url_str,
                        status_code=result.status_code,
                        response_time=result.response_time,
                        depth=depth,
                    )
                    if result.html:
                        parsed = parse_html(crawl_url_str, result.html, base_url)
                        parsed._fetch_result = result  # attach for analyzers
                        page.title = parsed.title
                        page.meta_description = parsed.meta_description
                        page.content_length = parsed.html_length
                        page.word_count = parsed.word_count
                        parsed_pages.append(parsed)

                        # Enqueue internal links
                        if depth < max_depth:
                            for link in parsed.internal_links:
                                norm = normalize_url(link)
                                if norm and norm not in visited and is_same_domain(norm, base_url):
                                    queue.append((norm, depth + 1))
                                    progress["pages_found"] = len(visited) + len(queue)

                    db.add(page)
                    await db.commit()

                progress["pages_crawled"] = len(visited)
                await asyncio.sleep(settings.POLITENESS_DELAY)

        while queue and len(visited) < max_pages:
            batch = []
            while queue and len(batch) < settings.MAX_CONCURRENT_REQUESTS:
                u, d = queue.popleft()
                if u not in visited:
                    batch.append((u, d))

            if not batch:
                break

            tasks = [crawl_url(u, d) for u, d in batch]
            await asyncio.gather(*tasks)

    progress["status"] = "analyzing"

    # Run analyzers
    from app.analyzers.technical import TechnicalAnalyzer
    from app.analyzers.onpage import OnPageAnalyzer
    from app.analyzers.content import ContentAnalyzer
    from app.analyzers.structured_data import StructuredDataAnalyzer
    from app.analyzers.performance import PerformanceAnalyzer
    from app.analyzers.security import SecurityAnalyzer
    from app.analyzers.accessibility import AccessibilityAnalyzer
    from app.analyzers.links import LinksAnalyzer
    from app.scoring.engine import calculate_scores
    from app.fixers.meta_tags import generate_meta_fixes
    from app.fixers.structured_data import generate_structured_data_fixes
    from app.fixers.sitemap_gen import generate_sitemap_fix
    from app.fixers.robots_gen import generate_robots_fix
    from app.fixers.headings import generate_heading_fixes
    from app.fixers.images import generate_image_fixes

    # Collect fetch results for site-level analysis
    fetch_results = []
    for p in parsed_pages:
        if hasattr(p, "_fetch_result"):
            fetch_results.append(p._fetch_result)

    analyzers = [
        TechnicalAnalyzer(),
        OnPageAnalyzer(),
        ContentAnalyzer(),
        PerformanceAnalyzer(),
        SecurityAnalyzer(),
        AccessibilityAnalyzer(),
        LinksAnalyzer(),
        StructuredDataAnalyzer(),
    ]

    all_issues = []
    for analyzer in analyzers:
        issues = analyzer.analyze(parsed_pages, base_url, fetch_results)
        all_issues.extend(issues)

    # Generate fixes
    all_fixes = []
    all_fixes.extend(generate_meta_fixes(parsed_pages))
    all_fixes.extend(generate_structured_data_fixes(parsed_pages, base_url))
    all_fixes.extend(generate_sitemap_fix(parsed_pages, base_url))
    all_fixes.extend(generate_robots_fix(base_url))
    all_fixes.extend(generate_heading_fixes(parsed_pages))
    all_fixes.extend(generate_image_fixes(parsed_pages))

    # Calculate scores
    scores = calculate_scores(all_issues, num_pages=len(parsed_pages))

    # Save to DB
    async with session_factory() as db:
        from app.models import Issue, Fix, CategoryScore, Severity
        for issue in all_issues:
            db.add(Issue(
                crawl_job_id=job_id,
                page_url=issue.page_url,
                category=issue.category,
                severity=Severity(issue.severity),
                rule=issue.rule,
                message=issue.message,
                details=issue.details,
            ))
        for fix in all_fixes:
            db.add(Fix(
                crawl_job_id=job_id,
                page_url=fix.get("page_url"),
                fix_type=fix["fix_type"],
                description=fix["description"],
                original=fix.get("original"),
                suggested=fix["suggested"],
            ))
        overall = sum(s["score"] * s["weight"] for s in scores) / sum(s["weight"] for s in scores) if scores else 0
        for s in scores:
            db.add(CategoryScore(
                crawl_job_id=job_id,
                category=s["category"],
                score=s["score"],
                weight=s["weight"],
            ))

        job = await db.get(CrawlJob, job_id)
        job.status = CrawlStatus.COMPLETE
        job.overall_score = round(overall, 1)
        job.pages_crawled = len(visited)
        job.pages_found = len(visited)
        job.completed_at = datetime.datetime.utcnow()
        await db.commit()

    progress["status"] = "complete"
    progress["overall_score"] = round(overall, 1)
