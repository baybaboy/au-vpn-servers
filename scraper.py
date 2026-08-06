import requests
from bs4 import BeautifulSoup
import re

URL = "https://publicvpnlist.com/country/australia/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "lxml")

# Find IP:PORT combinations
matches = re.findall(
    r'(\d{1,3}(?:\.\d{1,3}){3})\D+TCP\D+(\d{2,5})',
    soup.get_text(" ", strip=True),
    flags=re.IGNORECASE
)

servers = sorted(set(f"{ip}:{port}" for ip, port in matches))

with open("servers.txt", "w") as f:
    for server in servers:
        f.write(server + "\n")

print(f"Found {len(servers)} servers")
