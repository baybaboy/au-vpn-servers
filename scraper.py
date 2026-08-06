from playwright.sync_api import sync_playwright
import re

URL = "https://publicvpnlist.com/country/australia/"

servers = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="networkidle")

    html = page.content()

    # Find all download pages
    links = sorted(set(re.findall(r'/download/\d+/', html)))
    links = ["https://publicvpnlist.com" + link for link in links]

    print(f"Found {len(links)} download pages")

    for link in links:
        print("Opening:", link)

        page.goto(link, wait_until="networkidle")

        page_html = page.content()

        host = re.search(r'data-download-host="([^"]+)"', page_html)
        port = re.search(r'data-download-port="([^"]+)"', page_html)

        if host and port:
            server = f"{host.group(1)}:{port.group(1)}"
            print("FOUND:", server)
            servers.append(server)

    browser.close()

servers = sorted(set(servers))

with open("servers.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(servers))

print(f"Saved {len(servers)} servers")
