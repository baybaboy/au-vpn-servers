from playwright.sync_api import sync_playwright
import re

URL = "https://publicvpnlist.com/country/australia/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="networkidle")

    html = page.content()

    # Find all download pages
    links = sorted(set(re.findall(r'/download/\d+/', html)))
    links = ["https://publicvpnlist.com" + x for x in links]

    print(f"Found {len(links)} download pages")

    if not links:
        browser.close()
        exit()

    # Only inspect the first page
    page.goto(links[0], wait_until="networkidle")

    print("=" * 80)
    print(page.content())
    print("=" * 80)

    with open("page.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    browser.close()
