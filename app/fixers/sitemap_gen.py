from app.fixers.base import make_fix
from datetime import datetime


def generate_sitemap_fix(pages, base_url: str) -> list[dict]:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    today = datetime.utcnow().strftime("%Y-%m-%d")

    for page in pages:
        priority = "1.0" if page.url == base_url else "0.8" if page.url.count("/") <= 4 else "0.5"
        lines.append("  <url>")
        lines.append(f"    <loc>{page.url}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")

    lines.append("</urlset>")
    sitemap_xml = "\n".join(lines)

    return [make_fix(
        "sitemap",
        "Generated sitemap.xml from crawled pages",
        sitemap_xml,
    )]
