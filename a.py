import requests
from bs4 import BeautifulSoup

url = "https://aniworld.to/anime/stream/from-old-country-bumpkin-to-master-swordsman"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# "Episoden" başlıklı <ul> içindeki <a> taglarını bulalım
episodes_ul = None
for ul in soup.select("div.hosterSiteDirectNav#stream ul"):
    if ul.find("span") and "Episoden" in ul.find("span").text:
        episodes_ul = ul
        break

if episodes_ul:
    episode_links = episodes_ul.find_all("a")
    for a in episode_links:
        print(a.get("href"))
else:
    print("Episoden listesi bulunamadı!")
