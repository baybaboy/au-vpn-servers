from playwright.sync_api import sync_playwright

URL = "https://publicvpnlist.com/country/australia/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="networkidle")

    page.screenshot(path="page.png", full_page=True)

    html = page.content()
    import re

links = re.findall(r'href="(/download/\d+/)"', html)

with open("servers.txt", "w", encoding="utf-8") as f:
    for link in sorted(set(links)):
        f.write("https://publicvpnlist.com" + link + "\n")

print(f"Found {len(links)} download links")
