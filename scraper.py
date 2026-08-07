import requests
import socket
import json
import time

# ============================================================
# PublicVPNList Australia TCP OpenVPN Scraper
# ============================================================

API_URL = "https://publicvpnlist.com/api/v1/servers"

# How fresh a PublicVPNList result must be
FRESH_WITHIN = 259200  # 72 hours

# Your own connectivity test
SOCKET_TIMEOUT = 5

# Maximum servers requested per API page
PER_PAGE = 200


# ============================================================
# Load fixed servers
# ============================================================

servers = []

try:
    with open("fixed_servers.txt", "r", encoding="utf-8") as f:
        for line in f:
            server = line.strip()

            if server and ":" in server:
                servers.append(server)

    print(f"Loaded {len(servers)} fixed servers")

except FileNotFoundError:
    print("fixed_servers.txt not found")


# ============================================================
# Check TCP server
# ============================================================

def check_server(host, port, timeout=SOCKET_TIMEOUT):

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


# ============================================================
# Get Australia TCP OpenVPN servers from PublicVPNList
# ============================================================

def get_publicvpnlist_servers():

    discovered = []
    page = 1

    print("\nDownloading Australia TCP servers from PublicVPNList...")

    while True:

        params = {
            "country": "AU",
            "protocol": "openvpn",
            "transport": "tcp",
            "status": "online",
            "fresh_within": FRESH_WITHIN,
            "sort": "latency",
            "order": "asc",
            "page": page,
            "per_page": PER_PAGE,
            "format": "json",
        }

        try:
            response = requests.get(
                API_URL,
                params=params,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Australia-VPN-Scraper/2.0",
                },
                timeout=20,
            )

            if response.status_code == 429:
                print("Rate limited. Waiting 30 seconds...")
                time.sleep(30)
                continue

            response.raise_for_status()

            payload = response.json()

        except Exception as e:
            print(f"API request failed: {e}")
            break

        data = payload.get("data", [])

        if not data:
            break

        print(f"API page {page}: {len(data)} servers")
                # Debug: print the first API record on the first page
        if page == 1:
            print("\n===== FIRST API RECORD =====")
            print(json.dumps(data[0], indent=4))
            print("============================\n")

        for record in data:

            host = record.get("ip") or record.get("hostname")
            port = record.get("port")

            protocol = str(record.get("protocol", "")).lower()
            transport = str(record.get("transport", "")).lower()
            country = str(record.get("country_code", "")).upper()
            availability = str(record.get("availability_status", "")).lower()

            print(
                f"host={host} "
                f"port={port} "
                f"country={country} "
                f"protocol={protocol} "
                f"transport={transport} "
                f"availability={availability}"
            )

            if not host or not port:
                continue

            server = f"{host}:{int(port)}"
                        discovered.append(server)

        meta = payload.get("meta", {})

        current_page = meta.get("current_page", page)
        last_page = meta.get("last_page")

        if last_page is not None:
            if current_page >= last_page:
                break
        elif len(data) < PER_PAGE:
            break

        page += 1

    return discovered


# ============================================================
# Download current servers
# ============================================================

api_servers = get_publicvpnlist_servers()

print(
    f"\nPublicVPNList returned "
    f"{len(api_servers)} Australia TCP servers."
)


# Add API servers to fixed servers
servers.extend(api_servers)


# ============================================================
# Remove duplicates
# ============================================================

servers = sorted(
    set(
        s.strip()
        for s in servers
        if s.strip()
    )
)

print(
    f"Testing {len(servers)} unique servers..."
)


# ============================================================
# Test servers
# ============================================================

working_servers = []

for server in servers:

    try:

        host, port = server.rsplit(":", 1)

    except ValueError:

        print(f"Invalid server format: {server}")
        continue

    print(
        f"Testing {host}:{port}..."
    )

    online, latency = check_server(
        host,
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


# ============================================================
# Fastest first
# ============================================================

working_servers.sort(
    key=lambda x: x[1]
)


# ============================================================
# Save servers.txt
# ============================================================

with open(
    "servers.txt",
    "w",
    encoding="utf-8"
) as f:

    for server, latency in working_servers:

        f.write(
            server + "\n"
        )


# ============================================================
# Create Records.json
# ============================================================

records = []

for server, latency in working_servers:

    try:

        ip, port = server.rsplit(":", 1)

        port = int(port)

    except ValueError:

        continue


    # ========================================================
    # Score
    # ========================================================

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

        "PORT": port,

        "UPTIME": "100%",

        "PING": str(latency),

        "FLAG": "AU",

        "SESSIONS": 0,

        "LINE_QUALITY": 100,

        "SCORE": score

    })


# ============================================================
# Save Records.json
# ============================================================

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


# ============================================================
# Summary
# ============================================================

print("\n===================================")

print(
    f"Working servers: {len(records)}"
)

print(
    "Created servers.txt"
)

print(
    "Created Records.json"
)

print(
    "==================================="
)

print("Done!")
