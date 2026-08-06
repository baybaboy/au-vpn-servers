from playwright.sync_api import sync_playwright
import re
import socket
import json
from datetime import datetime

URL = "https://publicvpnlist.com/country/australia/"

servers = []


def check_server(host, port, timeout=5):
    try:
        sock = socket.create_connection((host, int(port)), timeout=timeout)
        sock.close()
        return True
    except:
        return False


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
        print(f"\nOpening: {link}")

        page.goto(link, wait_until="networkidle")

        page_html = page.content()

        host = re.search(r'data-download-host="([^"]+)"', page_html)
        port = re.search(r'data-download-port="([^"]+)"', page_html)

        if host and port:
            ip = host.group(1)
            portnum = port.group(1)

            print(f"Testing {ip}:{portnum}...")

            if check_server(ip, portnum):
                print(f"✓ ONLINE {ip}:{portnum}")
                servers.append(f"{ip}:{portnum}")
            else:
                print(f"✗ OFFLINE {ip}:{portnum}")

    browser.close()

# Remove duplicates
servers = sorted(set(servers))

# Save TXT
with open("servers.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(servers))

# Build JSON
json_servers = []

for server in servers:
    ip, port = server.split(":")
    json_servers.append({
        "ip": ip,
        "port": int(port),
        "country": "Australia",
        "protocol": "TCP",
        "status": "online"
    })

data = {
    "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "total_servers": len(json_servers),
    "servers": json_servers
}

with open("servers.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

print("\n===================================")
print(f"Working servers: {len(servers)}")
print("Created servers.txt")
print("Created servers.json")
print("Done!")
