from app.fixers.base import make_fix


def generate_heading_fixes(pages) -> list[dict]:
    fixes = []
    for page in pages:
        if not page.h1s:
            suggested = page.title or "Page Heading"
            fixes.append(make_fix(
                "heading",
                "Add H1 heading to page",
                f"<h1>{suggested}</h1>",
                page_url=page.url,
            ))

        # Check heading hierarchy
        if page.headings:
            prev_level = 0
            fixed_headings = []
            needs_fix = False
            for tag, text in page.headings:
                level = int(tag[1])
                if level > prev_level + 1 and prev_level > 0:
                    needs_fix = True
                    correct_level = prev_level + 1
                    fixed_headings.append((f"h{correct_level}", text))
                else:
                    fixed_headings.append((tag, text))
                prev_level = int(fixed_headings[-1][0][1])

            if needs_fix:
                original = "\n".join(f"<{t}>{text}</{t}>" for t, text in page.headings)
                suggested = "\n".join(f"<{t}>{text}</{t}>" for t, text in fixed_headings)
                fixes.append(make_fix(
                    "heading",
                    "Fix heading hierarchy (skipped levels)",
                    suggested,
                    page_url=page.url,
                    original=original,
                ))

    return fixes
