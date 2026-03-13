"""
Screenshot demo script for SEO Optimizer.
Starts the server with a fresh database, runs a crawl on a test site,
and captures viewport-sized screenshots for the GitHub README.

Usage: python take_screenshots.py [url]
Default URL: https://example.com
"""

import sys
import asyncio
import time
import subprocess
import json
import urllib.request
import urllib.error
from pathlib import Path

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
DATA_DIR = Path(__file__).parent / "data"
PORT = 8080
BASE = f"http://localhost:{PORT}"
DEFAULT_URL = "https://example.com"


def clean_database():
    db_path = DATA_DIR / "seo.db"
    if db_path.exists():
        db_path.unlink()
        print("  Removed old database.")


def wait_for_server(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"{BASE}/api/crawl/", timeout=2)
            return True
        except urllib.error.URLError:
            time.sleep(0.5)
    return False


def start_crawl(url: str) -> int:
    data = json.dumps({"url": url, "max_pages": 20, "max_depth": 2}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/crawl/",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["id"]


def wait_for_crawl(job_id: int, timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        resp = urllib.request.urlopen(f"{BASE}/api/crawl/{job_id}")
        job = json.loads(resp.read())
        status = job["status"]
        pages = job["pages_crawled"]
        print(f"  Status: {status} | Pages crawled: {pages}    ", end="\r")
        if status == "complete":
            print(f"\n  Crawl complete! Score: {job['overall_score']}")
            return True
        if status == "failed":
            print(f"\n  Crawl failed: {job.get('error_message')}")
            return False
        time.sleep(2)
    print("\n  Timeout waiting for crawl.")
    return False


async def take_screenshots(job_id: int):
    from playwright.async_api import async_playwright

    SCREENSHOTS_DIR.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        # 1. Dashboard
        print("  Capturing: dashboard...")
        await page.goto(BASE, wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "dashboard.png"))

        # 2. Report overview — top of page with score + category cards
        print("  Capturing: report overview...")
        await page.goto(f"{BASE}/report/{job_id}", wait_until="networkidle")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "report-overview.png"))

        # 3. Score distribution — scroll to show radar chart centered
        print("  Capturing: score details...")
        radar = page.locator("#radarChart")
        if await radar.count() > 0:
            await radar.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            # Scroll up a bit so the chart title is visible
            await page.evaluate("window.scrollBy(0, -80)")
            await page.wait_for_timeout(300)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "score-details.png"))

        # For each tab: click tab, then scroll so the tab bar is at the
        # top of the viewport and the tab content fills the screenshot.

        async def capture_tab(tab_text: str, filename: str):
            btn = page.locator("button", has_text=tab_text)
            if await btn.count() > 0:
                await btn.click()
                await page.wait_for_timeout(800)
            # Scroll the tab bar to the very top of the viewport
            await page.evaluate("""
                const tabBar = document.querySelector('nav.-mb-px, .border-b nav');
                if (tabBar) {
                    const rect = tabBar.getBoundingClientRect();
                    window.scrollBy(0, rect.top - 10);
                }
            """)
            await page.wait_for_timeout(400)
            await page.screenshot(path=str(SCREENSHOTS_DIR / filename))

        # 4. Issues tab
        print("  Capturing: issues tab...")
        await capture_tab("Issues", "issues.png")

        # 5. Pages tab
        print("  Capturing: pages tab...")
        await capture_tab("Pages", "pages.png")

        # 6. Fixes tab
        print("  Capturing: fixes tab...")
        await capture_tab("Fixes", "fixes.png")

        await browser.close()

    print(f"\n  Screenshots saved to {SCREENSHOTS_DIR.resolve()}/")


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL

    print("[1/5] Cleaning old data...")
    clean_database()

    print(f"[2/5] Starting server on port {PORT}...")
    server = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        if not wait_for_server():
            print("ERROR: Server failed to start.")
            return 1

        print(f"[3/5] Starting crawl of {url} (max 20 pages)...")
        job_id = start_crawl(url)
        print(f"  Job ID: {job_id}")

        if not wait_for_crawl(job_id):
            return 1

        print("[4/5] Taking screenshots...")
        asyncio.run(take_screenshots(job_id))

        print("[5/5] Done! Screenshots ready for README.")
        return 0

    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    sys.exit(main() or 0)
