from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "SEO Optimizer"
    DATABASE_URL: str = f"sqlite+aiosqlite:///{Path(__file__).parent.parent / 'data' / 'seo.db'}".replace("\\", "/")
    MAX_CONCURRENT_REQUESTS: int = 5
    POLITENESS_DELAY: float = 1.0
    MAX_PAGES: int = 100
    MAX_DEPTH: int = 5
    REQUEST_TIMEOUT: int = 30
    USER_AGENT: str = "SEOOptimizer/1.0 (+https://github.com/seo-optimizer)"


settings = Settings()
