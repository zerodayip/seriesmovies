import requests
from bs4 import BeautifulSoup

url = "https://filmkovasi.pw/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

try:
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Sadece ana sayfadaki .listmovie bloklarını çek
    listmovie_blocks = soup.find_all("div", class_="listmovie")
    
    # Her birini yazdır
    for block in listmovie_blocks:
        print(block.prettify())  # Dilersen .prettify() olmadan ham HTML de yazdırabilirsin

except Exception as e:
    print(f"Hata: {e}")
