from urllib.parse import urlparse, urljoin, urldefrag, parse_qs, urlencode, urlunparse


def normalize_url(url: str, base_url: str | None = None) -> str | None:
    if base_url:
        url = urljoin(base_url, url)
    url, _ = urldefrag(url)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    path = parsed.path.rstrip("/") or "/"
    query = urlencode(sorted(parse_qs(parsed.query, keep_blank_values=True).items()), doseq=True)
    normalized = urlunparse((parsed.scheme, parsed.netloc.lower(), path, parsed.params, query, ""))
    return normalized


def is_same_domain(url: str, base_url: str) -> bool:
    return urlparse(url).netloc.lower() == urlparse(base_url).netloc.lower()


def get_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def is_crawlable_content_type(content_type: str | None) -> bool:
    if not content_type:
        return False
    return "text/html" in content_type.lower()
