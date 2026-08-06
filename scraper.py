from playwright.sync_api import sync_playwright
import requests
import re

URL = "https://publicvpnlist.com/country/australia/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="networkidle")

    html = page.content()

    # Find download links
    download_links = sorted(set(re.findall(r'https://publicvpnlist\.com/download/\d+/', html)))

    servers = []

    for link in download_links:
        try:
            print("Checking:", link)

            r = requests.get(link, timeout=20, allow_redirects=True)

print("Checking:", link)
print("Final URL:", r.url)

with open("download.txt", "w", encoding="utf-8") as f:
    f.write(r.text)

m = re.search(r"remote\s+([^\s]+)\s+(\d+)", r.text)

            if m:
                server = m.group(1)
                port = m.group(2)
                servers.append(f"{server}:{port}")

        except Exception as e:
            print(e)

    browser.close()

servers = sorted(set(servers))

with open("servers.txt", "w") as f:
    f.write("\n".join(servers))

print(f"Found {len(servers)} servers")
