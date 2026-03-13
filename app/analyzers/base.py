from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class IssueFound:
    category: str
    severity: str  # "critical", "warning", "info"
    rule: str
    message: str
    page_url: str | None = None
    details: str | None = None


class BaseAnalyzer(ABC):
    category: str = ""

    @abstractmethod
    def analyze(self, pages: list, base_url: str, fetch_results: list | None = None) -> list[IssueFound]:
        pass

    def issue(self, severity: str, rule: str, message: str, page_url: str | None = None, details: str | None = None) -> IssueFound:
        return IssueFound(
            category=self.category,
            severity=severity,
            rule=rule,
            message=message,
            page_url=page_url,
            details=details,
        )
