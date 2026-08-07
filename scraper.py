from playwright.sync_api import sync_playwright
import re
import socket
import json
import time

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
        start = time.time()

        sock = socket.create_connection(
            (host, int(port)),
            timeout=timeout
        )

        sock.close()

        latency = int((time.time() - start) * 1000)

        return True, latency

    except Exception:
        return False, None


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

print(f"\nTesting {len(servers)} unique servers...")

working_servers = []

for server in servers:

    ip, port = server.split(":")

    print(f"Testing {ip}:{port}...")

    online, latency = check_server(ip, port)

    if online:
        print(f"✓ ONLINE ({latency} ms)")
        working_servers.append((server, latency))
    else:
        print("✗ OFFLINE")

# Fastest first
working_servers.sort(key=lambda x: x[1])

# Save servers.txt
with open("servers.txt", "w", encoding="utf-8") as f:
    for server, latency in working_servers:
        f.write(server + "\n")

records = []

for server, latency in working_servers:

    ip, port = server.split(":")

    if latency <= 100:
        score = 100
    elif latency <= 200:
        score = 90
    elif latency <= 300:
        score = 80
    elif latency <= 500:
        score = 70
    else:
        score = 60

    records.append({
        "LOCATION": "Australia",
        "HOSTNAME": ip,
        "PORT": int(port),
        "UPTIME": "100%",
        "PING": str(latency),
        "FLAG": "AU",
        "SESSIONS": 0,
        "LINE_QUALITY": 100,
        "SCORE": score
    })

with open("Records.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=4)

print("\n===================================")
print(f"Working servers: {len(records)}")
print("Created servers.txt")
print("Created Records.json")
print("Done!")
