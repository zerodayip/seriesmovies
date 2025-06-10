import requests
from bs4 import BeautifulSoup

url = "https://filmmakinesi.de/film/amator-izle-2025-fm1/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    print(soup.prettify())  # Tam HTML çıktısını yazdırır
else:
    print(f"❌ HTTP {response.status_code} - Sayfa alınamadı.")
