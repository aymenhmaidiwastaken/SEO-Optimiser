from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 100
    max_depth: int = 5


class CrawlJobResponse(BaseModel):
    id: int
    url: str
    status: str
    overall_score: Optional[float] = None
    pages_crawled: int
    pages_found: int
    max_pages: int
    max_depth: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class PageResponse(BaseModel):
    id: int
    url: str
    status_code: Optional[int] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    content_length: Optional[int] = None
    response_time: Optional[float] = None
    depth: int
    word_count: Optional[int] = None

    class Config:
        from_attributes = True


class IssueResponse(BaseModel):
    id: int
    page_url: Optional[str] = None
    category: str
    severity: str
    rule: str
    message: str
    details: Optional[str] = None

    class Config:
        from_attributes = True


class FixResponse(BaseModel):
    id: int
    page_url: Optional[str] = None
    fix_type: str
    description: str
    original: Optional[str] = None
    suggested: str

    class Config:
        from_attributes = True


class CategoryScoreResponse(BaseModel):
    category: str
    score: float
    weight: float

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    job: CrawlJobResponse
    scores: list[CategoryScoreResponse]
    issues: list[IssueResponse]
    fixes: list[FixResponse]
    pages: list[PageResponse]
