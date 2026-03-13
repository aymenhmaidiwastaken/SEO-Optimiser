import aiohttp
import time
from dataclasses import dataclass
from app.config import settings


@dataclass
class FetchResult:
    url: str
    status_code: int
    content_type: str | None
    html: str | None
    headers: dict
    response_time: float
    error: str | None = None
    redirect_url: str | None = None


async def fetch_url(session: aiohttp.ClientSession, url: str) -> FetchResult:
    start = time.monotonic()
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT),
            allow_redirects=True,
            ssl=False,
        ) as resp:
            elapsed = time.monotonic() - start
            content_type = resp.headers.get("Content-Type", "")
            html = None
            if "text/html" in content_type.lower():
                html = await resp.text(errors="replace")
            redirect_url = str(resp.url) if str(resp.url) != url else None
            return FetchResult(
                url=url,
                status_code=resp.status,
                content_type=content_type,
                html=html,
                headers=dict(resp.headers),
                response_time=elapsed,
                redirect_url=redirect_url,
            )
    except aiohttp.ClientError as e:
        return FetchResult(
            url=url,
            status_code=0,
            content_type=None,
            html=None,
            headers={},
            response_time=time.monotonic() - start,
            error=str(e),
        )
    except Exception as e:
        return FetchResult(
            url=url,
            status_code=0,
            content_type=None,
            html=None,
            headers={},
            response_time=time.monotonic() - start,
            error=str(e),
        )
