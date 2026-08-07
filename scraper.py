from playwright.sync_api import sync_playwright
import re
import socket
import json

URL = "https://publicvpnlist.com/country/australia/"

servers = []

# Load fixed servers
try:
    with open("fixed_servers.txt", "r", encoding="utf-8") as f:
        for line in f:
            server = line.strip()
            if server:
                servers.append(server)

    print(f"Loaded {len(servers)} fixed servers")

except FileNotFoundError:
    print("fixed_servers.txt not found")


def check_server(host, port, timeout=5):
    try:
        sock = socket.create_connection((host, int(port)), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="domcontentloaded", timeout=15000)

    html = page.content()

    links = sorted(set(re.findall(r'/download/\d+/', html)))
    links = ["https://publicvpnlist.com" + link for link in links]

    print(f"Found {len(links)} download pages")

    for link in links:
        print(f"\nOpening: {link}")

        try:
            page.goto(
                link,
                wait_until="domcontentloaded",
                timeout=10000
            )
        except Exception:
            print(f"Skipping timeout: {link}")
            continue

        page_html = page.content()

        host = re.search(r'data-download-host="([^"]+)"', page_html)
        port = re.search(r'data-download-port="([^"]+)"', page_html)

        if not host or not port:
            print("No server found")
            continue

        ip = host.group(1)
        portnum = port.group(1)

        servers.append(f"{ip}:{portnum}")

    browser.close()

# Remove duplicates
servers = sorted(set(servers))

print(f"\nTesting {len(servers)} servers...")

working_servers = []

for server in servers:
    ip, port = server.split(":")

    print(f"Testing {ip}:{port}...")

    if check_server(ip, port):
        print(f"✓ ONLINE {ip}:{port}")
        working_servers.append(server)
    else:
        print(f"✗ OFFLINE {ip}:{port}")

# Save servers.txt
with open("servers.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(working_servers))

# Build Records.json
records = []

for server in working_servers:
    ip, port = server.split(":")

    records.append({
        "LOCATION": "Australia",
        "HOSTNAME": ip,
        "PORT": int(port),
        "UPTIME": "100%",
        "PING": "20",
        "FLAG": "AU",
        "SESSIONS": 0,
        "LINE_QUALITY": 100,
        "SCORE": 100
    })

with open("Records.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=4)

print("\n===================================")
print(f"Working servers: {len(records)}")
print("Created servers.txt")
print("Created Records.json")
print("Done!")
