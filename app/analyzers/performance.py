from app.analyzers.base import BaseAnalyzer, IssueFound


class PerformanceAnalyzer(BaseAnalyzer):
    category = "Performance"

    def analyze(self, pages, base_url, fetch_results=None):
        issues = []
        total = max(len(pages), 1)

        large_pages = 0
        many_resources = 0
        blocking_js_pages = 0
        no_dimensions_pages = 0
        slow_pages = 0

        for page in pages:
            if page.html_length > 500_000:
                large_pages += 1

            total_resources = len(page.scripts) + len(page.stylesheets)
            if total_resources > 30:
                many_resources += 1

            blocking_scripts = [s for s in page.scripts if not s.get("async") and not s.get("defer")]
            if blocking_scripts:
                blocking_js_pages += 1

            no_dimensions = [img for img in page.images if not img.get("width") or not img.get("height")]
            if no_dimensions:
                no_dimensions_pages += 1

            if hasattr(page, '_fetch_result') and page._fetch_result.response_time > 3.0:
                slow_pages += 1

        if large_pages > 0:
            issues.append(self.issue("warning", "large_page",
                f"{large_pages}/{total} pages exceed 500KB"))

        if many_resources > 0:
            issues.append(self.issue("warning", "too_many_resources",
                f"{many_resources}/{total} pages load 30+ scripts/stylesheets"))

        if blocking_js_pages > 0:
            pct = blocking_js_pages / total * 100
            severity = "info"  # Common, not critical
            issues.append(self.issue(severity, "render_blocking_js",
                f"{blocking_js_pages}/{total} pages have render-blocking JavaScript"))

        if no_dimensions_pages > 0:
            issues.append(self.issue("info", "images_no_dimensions",
                f"{no_dimensions_pages}/{total} pages have images without explicit dimensions"))

        if slow_pages > 0:
            severity = "warning" if slow_pages > total * 0.2 else "info"
            issues.append(self.issue(severity, "slow_response",
                f"{slow_pages}/{total} pages have response times >3s"))

        return issues
