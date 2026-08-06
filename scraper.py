from playwright.sync_api import sync_playwright

URL = "https://publicvpnlist.com/country/australia/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="networkidle")

    page.screenshot(path="page.png", full_page=True)

    html = page.content()
    with open("page.html", "w", encoding="utf-8") as f:
        f.write(html)

    servers = []

    for line in html.splitlines():
        if "ovpn" in line.lower():
            servers.append(line.strip())

    with open("servers.txt", "w", encoding="utf-8") as f:
        if servers:
            f.write("\n".join(servers))
        else:
            f.write("No servers found")

    print(f"Found {len(servers)} server entries")

    browser.close()
