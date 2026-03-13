from app.fixers.base import make_fix


def generate_meta_fixes(pages) -> list[dict]:
    fixes = []
    for page in pages:
        # Title fix
        if not page.title or len(page.title) < 10:
            # Generate from H1 or URL
            suggested_title = page.h1s[0] if page.h1s else page.url.split("/")[-1].replace("-", " ").title()
            if len(suggested_title) > 60:
                suggested_title = suggested_title[:57] + "..."
            fixes.append(make_fix(
                "meta_title",
                f"Add optimized title tag",
                f'<title>{suggested_title}</title>',
                page_url=page.url,
                original=f'<title>{page.title}</title>' if page.title else None,
            ))
        elif len(page.title) > 60:
            truncated = page.title[:57] + "..."
            fixes.append(make_fix(
                "meta_title",
                f"Shorten title to under 60 characters",
                f'<title>{truncated}</title>',
                page_url=page.url,
                original=f'<title>{page.title}</title>',
            ))

        # Meta description fix
        if not page.meta_description:
            # Generate from first paragraph content
            desc = page.text_content[:155].strip() + "..." if page.text_content else ""
            if desc:
                fixes.append(make_fix(
                    "meta_description",
                    f"Add meta description",
                    f'<meta name="description" content="{desc}">',
                    page_url=page.url,
                ))
        elif len(page.meta_description) > 160:
            truncated = page.meta_description[:157] + "..."
            fixes.append(make_fix(
                "meta_description",
                f"Shorten meta description to under 160 characters",
                f'<meta name="description" content="{truncated}">',
                page_url=page.url,
                original=f'<meta name="description" content="{page.meta_description}">',
            ))

    return fixes
