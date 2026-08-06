import requests

url = "https://publicvpnlist.com/country/australia/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(url, headers=headers, timeout=30)

print("Status:", r.status_code)

with open("page.html", "w", encoding="utf-8") as f:
    f.write(r.text)

print("Downloaded", len(r.text), "bytes")
