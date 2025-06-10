import requests

url = "https://vctplay.site/manifests/lMWDCxaHOSVZ/master.m3u8"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://setfilmizle.nl"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    content = response.text.strip()
    print("✅ m3u8 içeriği veya linki:")
    print(content)
else:
    print(f"❌ HTTP {response.status_code} - Erişim reddedildi.")
