from app.analyzers.base import BaseAnalyzer, IssueFound


class AccessibilityAnalyzer(BaseAnalyzer):
    category = "Accessibility"

    def analyze(self, pages, base_url, fetch_results=None):
        issues = []

        # Track site-level patterns
        pages_missing_lang = 0
        pages_missing_alt = 0
        pages_no_landmarks = 0

        for page in pages:
            # Lang attribute
            if not page.lang:
                pages_missing_lang += 1

            # Alt text
            missing_alt = [img for img in page.images if img.get("alt") is None]
            if missing_alt:
                pages_missing_alt += 1

            # Form labels
            for form in page.forms:
                if form["input_count"] > 0 and form["label_count"] < form["input_count"]:
                    issues.append(self.issue("warning", "missing_form_labels",
                        f"Form has {form['input_count']} inputs but only {form['label_count']} labels",
                        page_url=page.url))

            # Semantic HTML + ARIA (only flag if completely absent)
            if not page.semantic_elements and page.aria_landmarks == 0:
                pages_no_landmarks += 1

        # Report as site-level summaries instead of per-page spam
        if pages_missing_lang > 0:
            pct = pages_missing_lang / max(len(pages), 1) * 100
            severity = "critical" if pct > 50 else "warning" if pct > 10 else "info"
            issues.append(self.issue(severity, "missing_lang",
                f"{pages_missing_lang}/{len(pages)} pages missing lang attribute on <html>"))

        if pages_missing_alt > 0:
            pct = pages_missing_alt / max(len(pages), 1) * 100
            severity = "warning" if pct > 30 else "info"
            issues.append(self.issue(severity, "missing_alt_text",
                f"{pages_missing_alt}/{len(pages)} pages have images without alt text"))

        if pages_no_landmarks > 0:
            pct = pages_no_landmarks / max(len(pages), 1) * 100
            if pct > 50:
                issues.append(self.issue("info", "no_landmarks",
                    f"{pages_no_landmarks}/{len(pages)} pages lack ARIA landmarks or semantic elements"))

        # Skip nav — site-level check (check homepage only)
        if pages and not pages[0].has_skip_nav:
            issues.append(self.issue("info", "missing_skip_nav",
                "No skip navigation link found on homepage"))

        return issues
