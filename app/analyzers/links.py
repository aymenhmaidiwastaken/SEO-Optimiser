from app.analyzers.base import BaseAnalyzer, IssueFound


class LinksAnalyzer(BaseAnalyzer):
    category = "Links"

    def analyze(self, pages, base_url, fetch_results=None):
        issues = []
        fetch_results = fetch_results or []
        total = max(len(pages), 1)

        # Build sets
        error_urls = {fr.url for fr in fetch_results if fr.status_code >= 400 or fr.error}
        redirect_urls = {fr.url for fr in fetch_results if fr.redirect_url}
        linked_pages = set()

        pages_with_broken = 0
        pages_with_redirect_links = 0
        pages_with_nofollow = 0

        for page in pages:
            for link in page.internal_links:
                linked_pages.add(link)

            broken = [l for l in page.internal_links if l in error_urls]
            if broken:
                pages_with_broken += 1

            redirect_links = [l for l in page.internal_links if l in redirect_urls]
            if redirect_links:
                pages_with_redirect_links += 1

            nofollow_internal = [
                l for l in page.links
                if l.get("is_internal") and "nofollow" in (l.get("rel") or [])
            ]
            if nofollow_internal:
                pages_with_nofollow += 1

        if pages_with_broken > 0:
            issues.append(self.issue("warning", "broken_internal_link",
                f"{pages_with_broken} pages contain broken internal links"))

        if pages_with_redirect_links > 0:
            issues.append(self.issue("info", "redirect_links",
                f"{pages_with_redirect_links} pages link to URLs that redirect"))

        if pages_with_nofollow > 0:
            issues.append(self.issue("info", "nofollow_internal",
                f"{pages_with_nofollow} pages have internal links with nofollow"))

        # Orphan pages
        orphan_pages = [p for p in pages if p.url != base_url and p.url not in linked_pages]
        if orphan_pages:
            issues.append(self.issue("info", "orphan_pages",
                f"{len(orphan_pages)} pages not linked from any other crawled page"))

        return issues
