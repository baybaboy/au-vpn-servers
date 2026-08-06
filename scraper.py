from playwright.sync_api import sync_playwright
import re
import os

URL = "https://publicvpnlist.com/country/australia/"

servers = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()

    page.goto(URL, wait_until="networkidle")

    # Find every download page
    links = page.locator("a[href*='/download/']").evaluate_all(
        "els => els.map(e => e.href)"
    )

    links = sorted(set(links))

    print(f"Found {len(links)} download pages")

    for link in links:
        try:
            print("Opening:", link)

            page.goto(link, wait_until="networkidle")

            # Find the actual download button
            button = page.locator("a[href$='.ovpn'], a.download, a.btn")

            if button.count() == 0:
                print("No download button found")
                continue

            with page.expect_download() as download_info:
                button.first.click()

            download = download_info.value

            path = download.path()

            if not path:
                print("Download failed")
                continue

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                config = f.read()

            m = re.search(r"^remote\s+(\S+)\s+(\d+)", config, re.MULTILINE)

            if m:
                server = f"{m.group(1)}:{m.group(2)}"
                print("FOUND:", server)
                servers.append(server)

        except Exception as e:
            print("ERROR:", e)

    browser.close()

servers = sorted(set(servers))

with open("servers.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(servers))

print(f"Saved {len(servers)} servers")
