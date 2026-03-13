import asyncio
import json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.crawler.engine import crawl_progress

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/{job_id}")
async def progress_stream(job_id: int):
    async def event_generator():
        while True:
            progress = crawl_progress.get(job_id)
            if progress:
                yield {"event": "progress", "data": json.dumps(progress)}
                if progress.get("status") in ("complete", "failed"):
                    yield {"event": "done", "data": json.dumps(progress)}
                    break
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
