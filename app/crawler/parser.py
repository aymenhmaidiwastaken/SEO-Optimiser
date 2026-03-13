from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from app.crawler.url_utils import normalize_url
import re


@dataclass
class ParsedPage:
    url: str
    title: str | None = None
    meta_description: str | None = None
    meta_robots: str | None = None
    canonical: str | None = None
    h1s: list[str] = field(default_factory=list)
    h2s: list[str] = field(default_factory=list)
    headings: list[tuple[str, str]] = field(default_factory=list)  # (level, text)
    images: list[dict] = field(default_factory=list)  # [{src, alt}]
    links: list[dict] = field(default_factory=list)  # [{href, text, rel, is_internal}]
    internal_links: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)
    text_content: str = ""
    word_count: int = 0
    html_length: int = 0
    has_viewport: bool = False
    lang: str | None = None
    open_graph: dict = field(default_factory=dict)
    twitter_cards: dict = field(default_factory=dict)
    json_ld: list[dict] = field(default_factory=list)
    scripts: list[dict] = field(default_factory=list)
    stylesheets: list[str] = field(default_factory=list)
    forms: list[dict] = field(default_factory=list)
    has_skip_nav: bool = False
    semantic_elements: list[str] = field(default_factory=list)
    aria_landmarks: int = 0


def parse_html(url: str, html: str, base_url: str) -> ParsedPage:
    soup = BeautifulSoup(html, "lxml")
    page = ParsedPage(url=url, html_length=len(html))

    # Title
    title_tag = soup.find("title")
    page.title = title_tag.get_text(strip=True) if title_tag else None

    # Meta tags
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").lower()
        content = meta.get("content", "")
        if name == "description":
            page.meta_description = content
        elif name == "robots":
            page.meta_robots = content
        elif name == "viewport":
            page.has_viewport = True
        elif name.startswith("og:"):
            page.open_graph[name] = content
        elif name.startswith("twitter:"):
            page.twitter_cards[name] = content

    # Canonical
    canonical_tag = soup.find("link", rel="canonical")
    if canonical_tag:
        page.canonical = canonical_tag.get("href")

    # Lang
    html_tag = soup.find("html")
    if html_tag:
        page.lang = html_tag.get("lang")

    # Headings
    for level in range(1, 7):
        for h in soup.find_all(f"h{level}"):
            text = h.get_text(strip=True)
            page.headings.append((f"h{level}", text))
            if level == 1:
                page.h1s.append(text)
            elif level == 2:
                page.h2s.append(text)

    # Images
    for img in soup.find_all("img"):
        page.images.append({
            "src": img.get("src", ""),
            "alt": img.get("alt"),
            "width": img.get("width"),
            "height": img.get("height"),
        })

    # Links
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        normalized = normalize_url(href, base_url=url)
        if not normalized:
            continue
        from app.crawler.url_utils import is_same_domain
        is_internal = is_same_domain(normalized, base_url)
        link_data = {
            "href": normalized,
            "text": a.get_text(strip=True),
            "rel": a.get("rel", []),
            "is_internal": is_internal,
        }
        page.links.append(link_data)
        if is_internal:
            page.internal_links.append(normalized)
        else:
            page.external_links.append(normalized)

    # Text content
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    page.text_content = soup.get_text(separator=" ", strip=True)
    page.word_count = len(page.text_content.split())

    # JSON-LD
    import json
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
            if isinstance(data, list):
                page.json_ld.extend(data)
            else:
                page.json_ld.append(data)
        except (json.JSONDecodeError, TypeError):
            pass

    # Scripts and stylesheets
    for script in soup.find_all("script", src=True):
        page.scripts.append({
            "src": script.get("src"),
            "async": script.has_attr("async"),
            "defer": script.has_attr("defer"),
        })
    for link in soup.find_all("link", rel="stylesheet"):
        page.stylesheets.append(link.get("href", ""))

    # Forms
    for form in soup.find_all("form"):
        labels = form.find_all("label")
        inputs = form.find_all("input")
        page.forms.append({
            "action": form.get("action", ""),
            "label_count": len(labels),
            "input_count": len(inputs),
        })

    # Skip navigation
    first_link = soup.find("a")
    if first_link and first_link.get("href", "").startswith("#"):
        page.has_skip_nav = True

    # Semantic elements
    for tag_name in ["header", "nav", "main", "article", "section", "aside", "footer"]:
        if soup.find(tag_name):
            page.semantic_elements.append(tag_name)

    # ARIA landmarks
    page.aria_landmarks = len(soup.find_all(attrs={"role": True}))

    return page
