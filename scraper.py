from playwright.sync_api import sync_playwright
import re
import socket
import json
import time
import urllib.request
import csv
import io
import base64

URL = "https://publicvpnlist.com/country/australia/"
VPN_GATE_URL = "http://www.vpngate.net/api/iphone/"

servers = []


# ------------------------------------------------------------
# Load fixed servers
# ------------------------------------------------------------
try:
    with open("fixed_servers.txt", "r", encoding="utf-8") as f:
        for line in f:
            server = line.strip()
            if server:
                servers.append(server)

    print(f"Loaded {len(servers)} fixed servers")

except FileNotFoundError:
    print("fixed_servers.txt not found")


# ------------------------------------------------------------
# Test TCP server
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# VPN Gate
#
# VPN Gate's API does not simply provide one universal TCP port
# field. Its OpenVPN configuration is included as Base64 data.
# We decode that configuration and extract TCP "remote" entries.
# Only Australia (AU) entries are added.
# ------------------------------------------------------------
def load_vpngate_australia():
    found = 0
    added = 0

    try:
        print("\nDownloading VPN Gate API...")

        request = urllib.request.Request(
            VPN_GATE_URL,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read().decode("utf-8", errors="replace")

        # VPN Gate CSV has comment/header lines before the actual CSV.
        lines = [
            line for line in data.splitlines()
            if line.strip() and not line.startswith("*")
        ]

        if not lines:
            print("VPN Gate returned no data")
            return

        # Find the CSV header.
        header_index = None
        for i, line in enumerate(lines):
            if "HostName" in line and "CountryShort" in line:
                header_index = i
                break

        if header_index is None:
            print("Could not find VPN Gate CSV header")
            return

        csv_text = "\n".join(lines[header_index:])

        reader = csv.DictReader(io.StringIO(csv_text))

        for row in reader:
            country = (row.get("CountryShort") or "").strip().upper()

            if country != "AU":
                continue

            found += 1

            config_b64 = (
                row.get("OpenVPN_ConfigData_Base64") or ""
            ).strip()

            if not config_b64:
                continue

            try:
                config = base64.b64decode(
                    config_b64
                ).decode("utf-8", errors="replace")
            except Exception:
                continue

            # Look for TCP OpenVPN configurations.
            tcp_mode = bool(
                re.search(
                    r"(?mi)^\s*(proto\s+tcp(?:-client)?|tcp-client)\b",
                    config
                )
            )

            if not tcp_mode:
                continue

            # Extract remote host + port from the OpenVPN config.
            remotes = re.findall(
                r"(?mi)^\s*remote\s+([^\s]+)\s+(\d+)(?:\s|$)",
                config
            )

            # Fallback to the API IP if the config's remote is missing.
            if not remotes:
                ip = (row.get("IP") or "").strip()
                if ip:
                    # Common VPN Gate TCP port. We only use this fallback
                    # when the config itself did not expose a remote entry.
                    remotes = [(ip, "443")]

            for host, port in remotes:
                # Only accept a valid host/port pair.
                try:
                    int(port)
                except ValueError:
                    continue

                server = f"{host}:{port}"

                if server not in servers:
                    servers.append(server)
                    added += 1

        print(
            f"VPN Gate Australia records found: {found}"
        )
        print(
            f"VPN Gate TCP endpoints added: {added}"
        )

    except Exception as e:
        print(f"VPN Gate download failed: {e}")


# ------------------------------------------------------------
# Load VPN Gate Australia servers
# ------------------------------------------------------------
load_vpngate_australia()


# ------------------------------------------------------------
# PublicVPNList Australia
# ------------------------------------------------------------
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    try:
        page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=15000
        )

        # The server table is populated by client-side JS after
        # the initial HTML loads.
        try:
            page.wait_for_selector(
                'a[href*="/download/"]',
                timeout=15000
            )
        except Exception:
            print(
                "Warning: no download links appeared within timeout "
                "— site may be slow or layout changed"
            )

        html = page.content()

        links = sorted(
            set(
                re.findall(
                    r'/download/\d+/',
                    html
                )
            )
        )

        links = [
            "https://publicvpnlist.com" + link
            for link in links
        ]

        print(
            f"Found {len(links)} PublicVPNList download pages"
        )

        for link in links:
            print(f"\nOpening: {link}")

            try:
                page.goto(
                    link,
                    wait_until="domcontentloaded",
                    timeout=10000
                )

                page.wait_for_selector(
                    '[data-download-host]',
                    timeout=10000
                )

            except Exception:
                print(f"Skipping timeout: {link}")
                continue

            page_html = page.content()

            host = re.search(
                r'data-download-host="([^"]+)"',
                page_html
            )

            port = re.search(
                r'data-download-port="([^"]+)"',
                page_html
            )

            if not host or not port:
                print("No server found")
                continue

            ip = host.group(1)
            portnum = port.group(1)

            servers.append(
                f"{ip}:{portnum}"
            )

    except Exception as e:
        print(f"PublicVPNList error: {e}")

    finally:
        browser.close()


# ------------------------------------------------------------
# Remove duplicates
# ------------------------------------------------------------
servers = sorted(set(servers))

print(
    f"\nTesting {len(servers)} unique servers..."
)


# ------------------------------------------------------------
# Test all TCP endpoints
# ------------------------------------------------------------
working_servers = []

for server in servers:

    try:
        ip, port = server.rsplit(":", 1)
    except ValueError:
        print(f"Skipping invalid server: {server}")
        continue

    print(f"Testing {ip}:{port}...")

    online, latency = check_server(
        ip,
        port
    )

    if online:
        print(
            f"✓ ONLINE ({latency} ms)"
        )

        working_servers.append(
            (server, latency)
        )

    else:
        print("✗ OFFLINE")


# ------------------------------------------------------------
# Fastest first
# ------------------------------------------------------------
working_servers.sort(
    key=lambda x: x[1]
)


# ------------------------------------------------------------
# Save servers.txt
# ------------------------------------------------------------
with open(
    "servers.txt",
    "w",
    encoding="utf-8"
) as f:

    for server, latency in working_servers:
        f.write(server + "\n")


# ------------------------------------------------------------
# Build Records.json
# ------------------------------------------------------------
records = []

for server, latency in working_servers:

    ip, port = server.rsplit(":", 1)

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


# ------------------------------------------------------------
# Save Records.json
# ------------------------------------------------------------
with open(
    "Records.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        records,
        f,
        indent=4
    )


# ------------------------------------------------------------
# Done
# ------------------------------------------------------------
print("\n===================================")
print(
    f"Working servers: {len(records)}"
)
print("Created servers.txt")
print("Created Records.json")
print("Done!")
                
