import requests
from bs4 import BeautifulSoup

video_url = "https://www.animeizlesene.com/serie/kusuriya-no-hitorigoto-484-2-season-21-episode"  # örnek bölüm!

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
}
resp = requests.get(video_url, headers=headers)
soup = BeautifulSoup(resp.text, "html.parser")

print("Tüm .parilda elementleri:", soup.select('.parilda'))
for el in soup.select('.parilda'):
    print("data-embed:", el.get('data-embed'))
