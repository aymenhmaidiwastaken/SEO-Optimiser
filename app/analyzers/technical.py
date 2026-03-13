from app.analyzers.base import BaseAnalyzer, IssueFound


class TechnicalAnalyzer(BaseAnalyzer):
    category = "Technical SEO"

    def analyze(self, pages, base_url, fetch_results=None):
        issues = []
        fetch_results = fetch_results or []
        total = max(len(pages), 1)

        # HTTPS (site-level)
        if base_url.startswith("http://"):
            issues.append(self.issue("critical", "no_https",
                "Site is not using HTTPS"))

        # Canonical — summarize
        missing_canonical = sum(1 for p in pages if not p.canonical)
        if missing_canonical > 0:
            pct = missing_canonical / total * 100
            severity = "warning" if pct > 50 else "info"
            issues.append(self.issue(severity, "missing_canonical",
                f"{missing_canonical}/{total} pages missing canonical tag"))

        # Viewport — summarize
        missing_viewport = sum(1 for p in pages if not p.has_viewport)
        if missing_viewport > 0:
            pct = missing_viewport / total * 100
            severity = "critical" if pct > 50 else "warning" if pct > 10 else "info"
            issues.append(self.issue(severity, "missing_viewport",
                f"{missing_viewport}/{total} pages missing viewport meta tag"))

        # Noindex pages
        noindex = [p for p in pages if p.meta_robots and "noindex" in p.meta_robots.lower()]
        if noindex:
            issues.append(self.issue("info", "noindex",
                f"{len(noindex)} pages set to noindex"))

        # Redirects — summarize
        redirects = [fr for fr in fetch_results if fr.redirect_url]
        if redirects:
            issues.append(self.issue("info", "redirects",
                f"{len(redirects)} URLs redirect to different locations"))

        # Slow responses
        slow = [fr for fr in fetch_results if fr.response_time > 3.0]
        if slow:
            issues.append(self.issue("warning", "slow_response",
                f"{len(slow)} pages have slow response times (>3s)"))

        # HTTP errors
        errors_4xx = [fr for fr in fetch_results if 400 <= fr.status_code < 500]
        errors_5xx = [fr for fr in fetch_results if fr.status_code >= 500]
        if errors_5xx:
            issues.append(self.issue("critical", "server_errors",
                f"{len(errors_5xx)} pages returned server errors (5xx)"))
        if errors_4xx:
            issues.append(self.issue("warning", "client_errors",
                f"{len(errors_4xx)} pages returned client errors (4xx)"))

        return issues
