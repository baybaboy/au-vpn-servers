import base64
import csv
import io
import json
import re
import socket
import time
import requests
from playwright.sync_api import sync_playwright

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


def get_vpngate_au_servers():
    """Fetches Australian TCP servers directly from VPN Gate."""
    print("\nFetching servers from VPN Gate API...")
    vpngate_servers = []
    try:
        url = "http://www.vpngate.net/api/iphone/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        lines = response.text.strip().splitlines()
        valid_lines = [line for line in lines if not line.startswith("*")]

        reader = csv.DictReader(io.StringIO("\n".join(valid_lines)))

        for row in reader:
            country_short = row.get("CountryShort", "").upper()
            country_long = row.get("CountryLong", "").lower()

            if country_short == "AU" or "australia" in country_long:
                ip = row.get("IP")
                config_b64 = row.get("OpenVPN_ConfigData_Base64")

                if not ip or not config_b64:
                    continue

                # Decode OpenVPN config file to locate TCP ports
                config_text = base64.b64decode(config_b64).decode(
                    "utf-8", errors="ignore"
                )

                is_tcp = "proto tcp" in config_text.lower()
                ports = re.findall(
                    r"^remote\s+\S+\s+(\d+)", config_text, re.MULTILINE
                )

                if is_tcp and ports:
                    vpngate_servers.append(f"{ip}:{ports[0]}")

        print(f"Found {len(vpngate_servers)} TCP servers on VPN Gate")
    except Exception as e:
        print(f"Error fetching VPN Gate servers: {e}")

    return vpngate_servers


def check_server(host, port, timeout=5):
    try:
        start = time.time()

        sock = socket.create_connection((host, int(port)), timeout=timeout)

        sock.close()

        latency = int((time.time() - start) * 1000)

        return True, latency

    except Exception:
        return False, None


# Fetch from VPN Gate
vpngate_list = get_vpngate_au_servers()
servers.extend(vpngate_list)

# Scrape PublicVPNList via Playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="domcontentloaded", timeout=15000)

    try:
        page.wait_for_selector('a[href*="/download/"]', timeout=15000)
    except Exception:
        print(
            "Warning: no download links appeared within timeout — site may be slow or layout changed"
        )

    html = page.content()

    links = sorted(set(re.findall(r"/download/\d+/", html)))
    links = ["https://publicvpnlist.com" + link for link in links]

    print(f"\nFound {len(links)} download pages on PublicVPNList")

    for link in links:
        print(f"Opening: {link}")

        try:
            page.goto(link, wait_until="domcontentloaded", timeout=10000)
            page.wait_for_selector("[data-download-host]", timeout=10000)
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

# Remove duplicates across all sources
servers = sorted(set(servers))

print(f"\nTesting {len(servers)} total unique servers across all sources...")

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

    records.append(
        {
            "LOCATION": "Australia",
            "HOSTNAME": ip,
            "PORT": int(port),
            "UPTIME": "100%",
            "PING": str(latency),
            "FLAG": "AU",
            "SESSIONS": 0,
            "LINE_QUALITY": 100,
            "SCORE": score,
        }
    )

with open("Records.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=4)

print("\n===================================")
print(f"Working servers: {len(records)}")
print("Created servers.txt")
print("Created Records.json")
print("Done!")
