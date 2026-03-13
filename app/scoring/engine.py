CATEGORY_WEIGHTS = {
    "Technical SEO": 0.20,
    "On-Page SEO": 0.20,
    "Content Quality": 0.15,
    "Structured Data": 0.10,
    "Performance": 0.10,
    "Security": 0.10,
    "Accessibility": 0.10,
    "Links": 0.05,
}

SEVERITY_WEIGHTS = {
    "critical": 3.0,
    "warning": 1.0,
    "info": 0.2,
}


def calculate_scores(issues: list, num_pages: int = 1) -> list[dict]:
    """
    Percentage-based scoring. For each category:
    - Count weighted issue points
    - Normalize by number of pages to get "issues per page"
    - Convert to a 0-100 score using a curve that matches real-world expectations

    A site with ~1 warning per page per category scores ~85.
    A site with ~3 warnings per page per category scores ~65.
    Only sites with many critical issues per page drop below 50.
    """
    num_pages = max(num_pages, 1)
    scores = []

    for category, weight in CATEGORY_WEIGHTS.items():
        cat_issues = [i for i in issues if i.category == category]

        if not cat_issues:
            scores.append({"category": category, "score": 100.0, "weight": weight})
            continue

        # Deduplicate site-level issues (no page_url) — count them once
        site_level_points = 0.0
        page_level_points = 0.0

        seen_site_rules = set()
        for issue in cat_issues:
            w = SEVERITY_WEIGHTS.get(issue.severity, 0.2)
            if not issue.page_url:
                if issue.rule not in seen_site_rules:
                    seen_site_rules.add(issue.rule)
                    site_level_points += w
            else:
                page_level_points += w

        # Normalize page-level issues by number of pages
        avg_page_points = page_level_points / num_pages

        # Total normalized severity: site-level (small fixed penalty) + per-page average
        total_severity = (site_level_points * 0.5) + avg_page_points

        # Convert to score using a decay curve:
        # score = 100 * e^(-k * severity)
        # k=0.15 means: severity 1 -> ~86, severity 3 -> ~64, severity 7 -> ~35
        import math
        score = 100.0 * math.exp(-0.15 * total_severity)
        score = max(0, min(100, round(score, 1)))

        scores.append({"category": category, "score": score, "weight": weight})

    return scores
