from app.fixers.base import make_fix


def generate_robots_fix(base_url: str) -> list[dict]:
    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {base_url.rstrip('/')}/sitemap.xml"""

    return [make_fix(
        "robots_txt",
        "Generated robots.txt with sitemap reference",
        robots_txt,
    )]
