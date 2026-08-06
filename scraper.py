from playwright.sync_api import sync_playwright

URL = "https://publicvpnlist.com/country/australia/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="networkidle")

    page.screenshot(path="page.png", full_page=True)

    with open("page.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    print("Saved page.html and page.png")

    browser.close()
