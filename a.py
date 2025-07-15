import requests
from bs4 import BeautifulSoup

url = "https://dizigom1.live/dizi-izle/rick-and-morty/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Sadece bölüm kısmı:
episodes_div = soup.select_one("div.serieEpisodes")
if episodes_div:
    html = episodes_div.prettify()
    print(html)  # Tümünü terminale basar
    # İstersen dosyaya da kaydedebilirsin:
    with open("rick_and_morty_bolumler.html", "w", encoding="utf-8") as f:
        f.write(html)
else:
    print("Bölümler div'i bulunamadı!")

