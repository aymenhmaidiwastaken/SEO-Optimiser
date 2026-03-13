from fastapi import APIRouter
from app.api.crawl import router as crawl_router
from app.api.reports import router as reports_router
from app.api.fixes import router as fixes_router
from app.api.ws import router as ws_router

api_router = APIRouter()
api_router.include_router(crawl_router)
api_router.include_router(reports_router)
api_router.include_router(fixes_router)
api_router.include_router(ws_router)
