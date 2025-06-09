import requests
from bs4 import BeautifulSoup

url = "https://filmkovasi.pw/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def extract_full_poster(img_tag):
    srcset = img_tag.get("data-srcset")
    if srcset:
        # En büyük (orijinal) boyutlu url
        url_list = [part.strip().split(' ')[0] for part in srcset.split(',')]
        for url in url_list:
            if '-180x270' not in url and '-152x270' not in url:
                return url
        return url_list[-1]
    return img_tag.get("data-src")

try:
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    for movie in soup.find_all("div", class_="listmovie"):
        movie_box = movie.find("div", class_="movie-box")
        if not movie_box:
            continue

        yil_div = movie_box.find("div", class_="film-yil")
        yil = yil_div.get_text(strip=True) if yil_div else ""

        img_tag = movie_box.find("img", class_="lazyload")
        poster_url = extract_full_poster(img_tag) if img_tag else ""

        film_ismi_div = movie_box.find("div", class_="film-ismi")
        a_tag = film_ismi_div.find("a") if film_ismi_div else None
        film_adi = a_tag.get_text(strip=True) if a_tag else ""
        film_link = a_tag.get("href") if a_tag else ""

        # IMDb puanı önce bolum-ust, yoksa imdb div'inde aranır
        imdb = ""
        bolum_ust = movie_box.find("div", class_="bolum-ust")
        if bolum_ust and bolum_ust.find("i", class_="fa-star"):
            imdb = bolum_ust.get_text(strip=True)
        elif movie_box.find("div", class_="imdb"):
            imdb = movie_box.find("div", class_="imdb").get_text(strip=True)

        print("Yıl:", yil)
        print("Poster:", poster_url)
        print("Film adı:", film_adi)
        print("Film link:", film_link)
        if imdb:
            print("IMDB:", imdb)
        print("-" * 50)

except Exception as e:
    print(f"Hata: {e}")
