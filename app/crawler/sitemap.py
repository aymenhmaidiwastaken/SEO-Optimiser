import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin


async def discover_sitemap_urls(session: aiohttp.ClientSession, base_url: str, sitemap_urls: list[str] | None = None) -> list[str]:
    urls = set()
    to_check = list(sitemap_urls or [])
    if not to_check:
        to_check = [
            urljoin(base_url, "/sitemap.xml"),
            urljoin(base_url, "/sitemap_index.xml"),
        ]

    checked = set()
    while to_check:
        sitemap_url = to_check.pop(0)
        if sitemap_url in checked:
            continue
        checked.add(sitemap_url)
        try:
            async with session.get(sitemap_url, timeout=aiohttp.ClientTimeout(total=10), ssl=False) as resp:
                if resp.status != 200:
                    continue
                text = await resp.text(errors="replace")
                soup = BeautifulSoup(text, "lxml-xml")

                # Sitemap index
                for sitemap in soup.find_all("sitemap"):
                    loc = sitemap.find("loc")
                    if loc:
                        to_check.append(loc.get_text(strip=True))

                # URL entries
                for url_tag in soup.find_all("url"):
                    loc = url_tag.find("loc")
                    if loc:
                        urls.add(loc.get_text(strip=True))
        except Exception:
            continue

    return list(urls)
