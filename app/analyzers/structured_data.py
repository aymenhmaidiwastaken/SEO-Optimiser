from app.analyzers.base import BaseAnalyzer, IssueFound


class StructuredDataAnalyzer(BaseAnalyzer):
    category = "Structured Data"

    def analyze(self, pages, base_url, fetch_results=None):
        issues = []

        # Track site-level: does ANY page have structured data?
        any_json_ld = any(p.json_ld for p in pages)
        any_og = any(p.open_graph for p in pages)

        # Site-level checks
        if not any_json_ld:
            issues.append(self.issue("warning", "no_json_ld_sitewide",
                "No JSON-LD structured data found on any page"))

        if not any_og:
            issues.append(self.issue("warning", "no_og_sitewide",
                "No Open Graph tags found on any page"))

        # Per-page checks — only for key pages (homepage + content pages, not pagination)
        for page in pages:
            # Skip pagination/category pages for per-page checks
            url_lower = page.url.lower()
            is_pagination = any(seg in url_lower for seg in ['/page/', '/category/'])
            if is_pagination:
                continue

            # JSON-LD — info level per page (not having it isn't critical)
            if not page.json_ld and page.word_count and page.word_count > 200:
                issues.append(self.issue("info", "missing_json_ld",
                    "No JSON-LD structured data", page_url=page.url))

            # Open Graph — only flag content pages missing it
            if not page.open_graph and page.word_count and page.word_count > 200:
                issues.append(self.issue("info", "missing_og",
                    "No Open Graph tags", page_url=page.url))
            elif page.open_graph:
                if "og:image" not in page.open_graph:
                    issues.append(self.issue("info", "missing_og_image",
                        "Missing og:image tag", page_url=page.url))

            # Twitter Cards — very minor
            if not page.twitter_cards and page.word_count and page.word_count > 300:
                issues.append(self.issue("info", "missing_twitter_cards",
                    "No Twitter Card tags", page_url=page.url))

        return issues
