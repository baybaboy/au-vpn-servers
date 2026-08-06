from playwright.sync_api import sync_playwright
import re

URL = "https://publicvpnlist.com/country/australia/"

servers = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="networkidle")

    html = page.content()

    download_links = sorted(set(re.findall(r'/download/\d+/', html)))
    download_links = [
        "https://publicvpnlist.com" + x
        for x in download_links
    ]

    print(f"Found {len(download_links)} download links")

    for link in download_links:
        print("Opening:", link)

        page.goto(link, wait_until="networkidle")

        text = page.content()

        # Save first page for debugging
        with open("page.html", "w", encoding="utf-8") as f:
            f.write(text)

        # Look for an OpenVPN config
        m = re.search(r"remote\s+([^\s]+)\s+(\d+)", text)

        if m:
            server = m.group(1)
            port = m.group(2)
            servers.append(f"{server}:{port}")
            print("FOUND:", f"{server}:{port}")



servers = sorted(set(servers))

with open("servers.txt", "w") as f:
    f.write("\n".join(servers))

print(f"Found {len(servers)} servers")
