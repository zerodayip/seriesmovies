import requests
from bs4 import BeautifulSoup

url = "https://filmkovasi.pw/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def extract_full_poster(img_tag):
    # En büyük (orijinal) poster url'sini bul
    srcset = img_tag.get("data-srcset")
    if srcset:
        for part in srcset.split(','):
            url = part.strip().split(' ')[0]
            if not '-180x270' in url:
                return url
        # Eğer yukarıda bulamazsa son kısmı al
        return srcset.split(',')[-1].strip().split(' ')[0]
    # data-src fallback
    return img_tag.get("data-src")

try:
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    for movie in soup.find_all("div", class_="listmovie"):
        # Film yılı
        yil_div = movie.find("div", class_="film-yil")
        yil = yil_div.get_text(strip=True) if yil_div else ""

        # Poster (tam boy)
        img_tag = movie.find("img", class_="lazyload")
        poster_url = extract_full_poster(img_tag) if img_tag else ""

        # Film adı ve sayfa linki
        film_ismi_div = movie.find("div", class_="film-ismi")
        a_tag = film_ismi_div.find("a") if film_ismi_div else None
        film_adi = a_tag.get_text(strip=True) if a_tag else ""
        film_link = a_tag.get("href") if a_tag else ""

        # IMDB puanı
        imdb_div = movie.find("div", class_="imdb")
        imdb = imdb_div.get_text(strip=True) if imdb_div else ""

        # Yazdır
        print("Yıl:", yil)
        print("Poster:", poster_url)
        print("Film adı:", film_adi)
        print("Film link:", film_link)
        if imdb:
            print("IMDB:", imdb)
        print("-" * 50)

except Exception as e:
    print(f"Hata: {e}")
