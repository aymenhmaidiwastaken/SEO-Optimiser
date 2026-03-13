from app.analyzers.base import BaseAnalyzer, IssueFound


class OnPageAnalyzer(BaseAnalyzer):
    category = "On-Page SEO"

    def analyze(self, pages, base_url, fetch_results=None):
        issues = []

        pages_missing_title = 0
        pages_missing_desc = 0
        pages_missing_h1 = 0
        pages_with_bad_headings = 0
        pages_missing_alt = 0

        for page in pages:
            # Title checks
            if not page.title:
                pages_missing_title += 1
            elif len(page.title) < 10:
                issues.append(self.issue("warning", "short_title",
                    f"Title too short ({len(page.title)} chars)", page_url=page.url))
            elif len(page.title) > 60:
                issues.append(self.issue("info", "long_title",
                    f"Title is {len(page.title)} chars (recommend 30-60)", page_url=page.url))

            # Meta description checks
            if not page.meta_description:
                pages_missing_desc += 1
            elif len(page.meta_description) < 50:
                issues.append(self.issue("info", "short_meta_description",
                    f"Meta description short ({len(page.meta_description)} chars)",
                    page_url=page.url))
            elif len(page.meta_description) > 160:
                issues.append(self.issue("info", "long_meta_description",
                    f"Meta description is {len(page.meta_description)} chars (recommend 120-160)",
                    page_url=page.url))

            # H1 checks
            if not page.h1s:
                pages_missing_h1 += 1
            elif len(page.h1s) > 1:
                issues.append(self.issue("info", "multiple_h1",
                    f"Multiple H1 tags ({len(page.h1s)})", page_url=page.url))

            # Heading hierarchy
            if page.headings:
                prev_level = 0
                for tag, text in page.headings:
                    level = int(tag[1])
                    if level > prev_level + 1 and prev_level > 0:
                        pages_with_bad_headings += 1
                        break
                    prev_level = level

            # Image alt text
            missing_alt = [img for img in page.images if not img.get("alt")]
            if missing_alt:
                pages_missing_alt += 1

        # Report summary issues
        total = max(len(pages), 1)

        if pages_missing_title > 0:
            pct = pages_missing_title / total * 100
            severity = "critical" if pct > 20 else "warning" if pct > 5 else "info"
            issues.append(self.issue(severity, "missing_title",
                f"{pages_missing_title}/{total} pages missing title tag"))

        if pages_missing_desc > 0:
            pct = pages_missing_desc / total * 100
            severity = "critical" if pct > 50 else "warning" if pct > 10 else "info"
            issues.append(self.issue(severity, "missing_meta_description",
                f"{pages_missing_desc}/{total} pages missing meta description"))

        if pages_missing_h1 > 0:
            pct = pages_missing_h1 / total * 100
            severity = "warning" if pct > 20 else "info"
            issues.append(self.issue(severity, "missing_h1",
                f"{pages_missing_h1}/{total} pages missing H1 heading"))

        if pages_with_bad_headings > 0:
            issues.append(self.issue("info", "heading_skip",
                f"{pages_with_bad_headings}/{total} pages have heading hierarchy gaps"))

        if pages_missing_alt > 0:
            pct = pages_missing_alt / total * 100
            severity = "warning" if pct > 30 else "info"
            issues.append(self.issue(severity, "missing_alt_text",
                f"{pages_missing_alt}/{total} pages have images without alt text"))

        # Duplicate titles
        titles = {}
        for page in pages:
            if page.title:
                titles.setdefault(page.title, []).append(page.url)
        dup_count = sum(len(urls) for urls in titles.values() if len(urls) > 1)
        if dup_count > 0:
            issues.append(self.issue("warning", "duplicate_title",
                f"{dup_count} pages share duplicate titles ({len([t for t,u in titles.items() if len(u)>1])} unique titles)"))

        # Duplicate descriptions
        descs = {}
        for page in pages:
            if page.meta_description:
                descs.setdefault(page.meta_description, []).append(page.url)
        dup_desc = sum(len(urls) for urls in descs.values() if len(urls) > 1)
        if dup_desc > 0:
            issues.append(self.issue("warning", "duplicate_description",
                f"{dup_desc} pages share duplicate meta descriptions"))

        return issues
