import aiohttp
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser


class AsyncRobotsChecker:
    def __init__(self):
        self._parsers: dict[str, RobotFileParser] = {}

    async def fetch_robots(self, session: aiohttp.ClientSession, base_url: str) -> RobotFileParser:
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    rp.parse(text.splitlines())
                else:
                    rp.parse([])
        except Exception:
            rp.parse([])
        self._parsers[parsed.netloc] = rp
        return rp

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        parsed = urlparse(url)
        rp = self._parsers.get(parsed.netloc)
        if rp is None:
            return True
        return rp.can_fetch(user_agent, url)

    def get_sitemaps(self, base_url: str) -> list[str]:
        parsed = urlparse(base_url)
        rp = self._parsers.get(parsed.netloc)
        if rp is None:
            return []
        return rp.site_maps() or []
