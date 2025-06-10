import requests
from bs4 import BeautifulSoup

# Hedef video linki
url = "https://vctplay.site/video/lMWDCxaHOSVZ"

# Gerekli headers (Referer + User-Agent)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Referer": "https://setfilmizle.nl"
}

# İstek gönder
response = requests.get(url, headers=headers)

# Duruma göre yanıtla
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    print(soup.prettify())  # veya print(soup.title)
else:
    print(f"❌ HTTP {response.status_code} - Sayfa alınamadı.")
