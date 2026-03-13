from app.analyzers.base import BaseAnalyzer, IssueFound


class SecurityAnalyzer(BaseAnalyzer):
    category = "Security"

    def analyze(self, pages, base_url, fetch_results=None):
        issues = []
        fetch_results = fetch_results or []

        # HTTPS check (site-level, once)
        if base_url.startswith("http://"):
            issues.append(self.issue("critical", "no_https",
                "Site is not served over HTTPS"))

        # Check security headers on FIRST page only (site-level config)
        if fetch_results:
            fr = fetch_results[0]
            headers = {k.lower(): v for k, v in fr.headers.items()}

            if "strict-transport-security" not in headers:
                issues.append(self.issue("info", "missing_hsts",
                    "Missing Strict-Transport-Security header"))

            if "content-security-policy" not in headers:
                issues.append(self.issue("info", "missing_csp",
                    "Missing Content-Security-Policy header"))

            if "x-frame-options" not in headers:
                issues.append(self.issue("info", "missing_x_frame_options",
                    "Missing X-Frame-Options header"))

            if "x-content-type-options" not in headers:
                issues.append(self.issue("info", "missing_x_content_type",
                    "Missing X-Content-Type-Options header"))

        # Mixed content check (only flag pages that actually have it)
        if base_url.startswith("https://"):
            for page in pages:
                has_mixed = False
                for img in page.images:
                    if img.get("src", "").startswith("http://"):
                        has_mixed = True
                        break
                for script in page.scripts:
                    if script.get("src", "").startswith("http://"):
                        issues.append(self.issue("warning", "mixed_content_script",
                            "Script loaded over HTTP", page_url=page.url))
                        break
                if has_mixed:
                    issues.append(self.issue("info", "mixed_content_image",
                        "Image loaded over HTTP", page_url=page.url))

        return issues
