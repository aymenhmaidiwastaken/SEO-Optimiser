import json
from app.fixers.base import make_fix


def generate_structured_data_fixes(pages, base_url: str) -> list[dict]:
    fixes = []

    # Organization schema for homepage
    org_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "url": base_url,
        "name": pages[0].title if pages else "Website",
    }
    fixes.append(make_fix(
        "json_ld",
        "Add Organization structured data to homepage",
        f'<script type="application/ld+json">\n{json.dumps(org_schema, indent=2)}\n</script>',
        page_url=base_url,
    ))

    for page in pages:
        if not page.json_ld:
            # WebPage schema
            webpage_schema = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": page.title or page.url,
                "url": page.url,
            }
            if page.meta_description:
                webpage_schema["description"] = page.meta_description
            fixes.append(make_fix(
                "json_ld",
                f"Add WebPage structured data",
                f'<script type="application/ld+json">\n{json.dumps(webpage_schema, indent=2)}\n</script>',
                page_url=page.url,
            ))

        # Open Graph fixes
        if not page.open_graph:
            og_tags = []
            og_tags.append(f'<meta property="og:title" content="{page.title or ""}">')
            og_tags.append(f'<meta property="og:description" content="{page.meta_description or ""}">')
            og_tags.append(f'<meta property="og:url" content="{page.url}">')
            og_tags.append('<meta property="og:type" content="website">')
            fixes.append(make_fix(
                "open_graph",
                f"Add Open Graph tags",
                "\n".join(og_tags),
                page_url=page.url,
            ))

    # BreadcrumbList for deeper pages
    deep_pages = [p for p in pages if p.url.count("/") > 3]
    for page in deep_pages[:10]:
        parts = page.url.replace(base_url, "").strip("/").split("/")
        items = []
        current = base_url
        for i, part in enumerate(parts):
            current = current.rstrip("/") + "/" + part
            items.append({
                "@type": "ListItem",
                "position": i + 1,
                "name": part.replace("-", " ").title(),
                "item": current,
            })
        if items:
            breadcrumb = {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": items,
            }
            fixes.append(make_fix(
                "json_ld",
                f"Add BreadcrumbList structured data",
                f'<script type="application/ld+json">\n{json.dumps(breadcrumb, indent=2)}\n</script>',
                page_url=page.url,
            ))

    return fixes
