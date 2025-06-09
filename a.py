import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

url = "https://filmkovasi.pw/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def extract_full_poster(img_tag):
    srcset = img_tag.get("data-srcset")
    if srcset:
        url_list = [part.strip().split(' ')[0] for part in srcset.split(',')]
        for url in url_list:
            if '-180x270' not in url and '-152x270' not in url:
                return url
        return url_list[-1]
    return img_tag.get("data-src")

def fetch_film_sources(film_link):
    out_lines = []
    page = 1
    while True:
        if page == 1:
            url = film_link
        else:
            if not film_link.endswith('/'):
                film_link += '/'
            url = film_link + f"{page}/"
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                break
            soup = BeautifulSoup(res.text, "html.parser")
            video_div = soup.find("div", class_="video-container")
            if not video_div:
                break

            m = re.search(r'<!--\s*baslik:(.*?)-->', str(video_div))
            baslik = m.group(1).strip() if m else "KAYNAK"

            iframe = video_div.find("iframe")
            if not iframe or not iframe.get("src"):
                break
            iframe_src = iframe["src"]

            out_lines.append(f"{baslik} : {iframe_src}")
            page += 1
        except Exception:
            break
    return out_lines

def process_movie(movie):
    movie_box = movie.find("div", class_="movie-box")
    if not movie_box:
        return ""
    yil_div = movie_box.find("div", class_="film-yil")
    yil = yil_div.get_text(strip=True) if yil_div else ""

    img_tag = movie_box.find("img", class_="lazyload")
    poster_url = extract_full_poster(img_tag) if img_tag else ""

    film_ismi_div = movie_box.find("div", class_="film-ismi")
    a_tag = film_ismi_div.find("a") if film_ismi_div else None
    film_adi = a_tag.get_text(strip=True) if a_tag else ""
    film_link = a_tag.get("href") if a_tag else ""

    imdb = ""
    bolum_ust = movie_box.find("div", class_="bolum-ust")
    if bolum_ust and bolum_ust.find("i", class_="fa-star"):
        imdb = bolum_ust.get_text(strip=True)
    elif movie_box.find("div", class_="imdb"):
        imdb = movie_box.find("div", class_="imdb").get_text(strip=True)

    output = []
    output.append(f"Yıl: {yil}")
    output.append(f"Poster: {poster_url}")
    output.append(f"Film adı: {film_adi}")
    output.append(f"Film link: {film_link}")
    if imdb:
        output.append(f"IMDB: {imdb}")

    # kaynakları çek
    if film_link:
        sources = fetch_film_sources(film_link)
        output.extend(sources)
    output.append("-" * 50)
    return "\n".join(output)

try:
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    movies = soup.find_all("div", class_="listmovie")
    # sadece ilk 10 film için paralel çalıştır
    max_parallel = 10
    results = []

    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        future_to_movie = {executor.submit(process_movie, movie): movie for movie in movies[:max_parallel]}
        for future in as_completed(future_to_movie):
            result = future.result()
            if result:
                results.append(result)

    for block in results:
        print(block)

except Exception as e:
    print(f"Hata: {e}")
