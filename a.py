import requests
from bs4 import BeautifulSoup

base_url = "https://aniworld.to"
page_url = "https://aniworld.to/anime/stream/from-old-country-bumpkin-to-master-swordsman"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
}

response = requests.get(page_url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

episodes_ul = None
for ul in soup.select("div.hosterSiteDirectNav#stream ul"):
    if ul.find("span") and "Episoden" in ul.find("span").text:
        episodes_ul = ul
        break

if episodes_ul:
    episode_links = episodes_ul.find_all("a")
    for a in episode_links:
        abs_link = requests.compat.urljoin(base_url, a.get("href"))
        print(abs_link)
else:
    print("Episoden listesi bulunamadı!")
