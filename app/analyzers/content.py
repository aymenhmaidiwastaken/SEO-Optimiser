from app.analyzers.base import BaseAnalyzer, IssueFound

try:
    import textstat
    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False


class ContentAnalyzer(BaseAnalyzer):
    category = "Content Quality"

    def analyze(self, pages, base_url, fetch_results=None):
        issues = []
        total = max(len(pages), 1)

        thin_pages = 0
        low_ratio_pages = 0
        poor_readability_pages = 0

        for page in pages:
            # Skip pagination/category listing pages for content analysis
            url_lower = page.url.lower()
            is_listing = any(seg in url_lower for seg in ['/page/', '/category/'])

            # Thin content (only flag non-listing pages)
            if not is_listing and page.word_count < 100:
                thin_pages += 1

            # Content-to-HTML ratio
            if page.html_length > 0:
                text_len = len(page.text_content.encode('utf-8'))
                ratio = text_len / page.html_length * 100
                if ratio < 10:
                    low_ratio_pages += 1

            # Readability
            if HAS_TEXTSTAT and page.text_content and page.word_count > 100 and not is_listing:
                try:
                    score = textstat.flesch_reading_ease(page.text_content)
                    if score < 30:
                        poor_readability_pages += 1
                except Exception:
                    pass

        # Report summaries
        if thin_pages > 0:
            pct = thin_pages / total * 100
            severity = "warning" if pct > 20 else "info"
            issues.append(self.issue(severity, "thin_content",
                f"{thin_pages}/{total} pages have thin content (<100 words)"))

        if low_ratio_pages > 0:
            pct = low_ratio_pages / total * 100
            severity = "warning" if pct > 50 else "info"
            issues.append(self.issue(severity, "low_content_ratio",
                f"{low_ratio_pages}/{total} pages have low text-to-HTML ratio (<10%)"))

        if poor_readability_pages > 0:
            issues.append(self.issue("info", "poor_readability",
                f"{poor_readability_pages}/{total} content pages have difficult readability (Flesch <30)"))

        # Duplicate content detection
        texts = [(p.url, p.text_content[:500].lower()) for p in pages if p.word_count and p.word_count > 50]
        dup_count = 0
        seen = set()
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                if texts[i][1] == texts[j][1] and texts[i][1] and texts[j][0] not in seen:
                    dup_count += 1
                    seen.add(texts[j][0])
        if dup_count > 0:
            issues.append(self.issue("warning", "duplicate_content",
                f"{dup_count} pages have near-duplicate content"))

        return issues
