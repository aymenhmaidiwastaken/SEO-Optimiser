import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class CrawlStatus(str, enum.Enum):
    PENDING = "pending"
    CRAWLING = "crawling"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    FAILED = "failed"


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False)
    status = Column(SAEnum(CrawlStatus), default=CrawlStatus.PENDING)
    overall_score = Column(Float, nullable=True)
    pages_crawled = Column(Integer, default=0)
    pages_found = Column(Integer, default=0)
    max_pages = Column(Integer, default=100)
    max_depth = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    pages = relationship("Page", back_populates="crawl_job", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="crawl_job", cascade="all, delete-orphan")
    fixes = relationship("Fix", back_populates="crawl_job", cascade="all, delete-orphan")
    scores = relationship("CategoryScore", back_populates="crawl_job", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crawl_job_id = Column(Integer, ForeignKey("crawl_jobs.id"), nullable=False)
    url = Column(String, nullable=False)
    status_code = Column(Integer, nullable=True)
    title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    content_length = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)
    depth = Column(Integer, default=0)
    word_count = Column(Integer, nullable=True)
    crawled_at = Column(DateTime, default=datetime.datetime.utcnow)

    crawl_job = relationship("CrawlJob", back_populates="pages")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crawl_job_id = Column(Integer, ForeignKey("crawl_jobs.id"), nullable=False)
    page_url = Column(String, nullable=True)
    category = Column(String, nullable=False)
    severity = Column(SAEnum(Severity), nullable=False)
    rule = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)

    crawl_job = relationship("CrawlJob", back_populates="issues")


class Fix(Base):
    __tablename__ = "fixes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crawl_job_id = Column(Integer, ForeignKey("crawl_jobs.id"), nullable=False)
    page_url = Column(String, nullable=True)
    fix_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    original = Column(Text, nullable=True)
    suggested = Column(Text, nullable=False)

    crawl_job = relationship("CrawlJob", back_populates="fixes")


class CategoryScore(Base):
    __tablename__ = "category_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crawl_job_id = Column(Integer, ForeignKey("crawl_jobs.id"), nullable=False)
    category = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, default=100.0)
    weight = Column(Float, nullable=False)

    crawl_job = relationship("CrawlJob", back_populates="scores")
