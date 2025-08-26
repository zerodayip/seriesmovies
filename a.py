import os
import re
import json
import requests
import time
from bs4 import BeautifulSoup
from collections import OrderedDict

# --------- Ayarlar ---------
GH_TOKEN = os.getenv("GH_TOKEN")
REPO = "zerodayip/m3u8file"

SERIES_PATHS = [
    "dizigomdizi.m3u",
    "sezonlukdizi.m3u",
    "rec/recdizi.m3u"
]
VOD_PATHS = [
    "dizigomfilmler.m3u",
    "setfilmizle.m3u",
    "rec/recfilm.m3u"
]

OUT_DIR = "xtream"
CACHE_SERIES = os.path.join(OUT_DIR, "imdb_series.json")
CACHE_VOD = os.path.join(OUT_DIR, "imdb_vod.json")

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36"
}
TIMEOUT = 15
# ---------------------------


def github_raw(path: str) -> str:
    """GitHub'dan dosya oku"""
    url = f"https://raw.githubusercontent.com/{REPO}/main/{path}"
    r = requests.get(url, headers=HTTP_HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def parse_m3u(content: str, is_series: bool = True) -> dict:
    """M3U içinden başlık ve varsa tvg-id çek"""
    entries = OrderedDict()
    lines = content.splitlines()

    for i, line in enumerate(lines):
        if line.startswith("#EXTINF:"):
            tvg_id_match = re.search(r'tvg-id="([^"]+)"', line)
            title = line.split(",")[-1].strip()

            entries[title] = {"imdb_id": None}
            if tvg_id_match:
                entries[title]["imdb_id"] = tvg_id_match.group(1)

    return entries


def load_cache(path: str) -> dict:
    """JSON cache yükle"""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(path: str, data: dict):
    """JSON cache kaydet"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def search_imdb_id_by_title(title: str) -> str | None:
    """IMDb'de başlıkla arama yap, ilk bulunan IMDb ID'yi döndür"""
    print(f"🔎 IMDb araması: {title}", flush=True)
    query = requests.utils.quote(title)
    url = f"https://www.imdb.com/find/?q={query}&s=tt"

    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print(f"⚠️ IMDb search hatası: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    first_result = soup.select_one(".findList .result_text a")

    if not first_result:
        return None

    href = first_result.get("href", "")
    m = re.search(r"/title/(tt\d+)/", href)
    if m:
        return m.group(1)
    return None


def fetch_title_poster(imdb_id: str) -> str | None:
    """IMDb title sayfasından poster URL çek"""
    url = f"https://www.imdb.com/title/{imdb_id}/"
    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print(f"⚠️ IMDb title hatası: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    img = soup.select_one(".ipc-image")

    if img and img.get("src"):
        return img["src"]

    return None


def process_files(paths: list[str], cache_file: str, is_series: bool = True):
    """M3U dosyalarını IMDb cache ile eşle"""
    cache = load_cache(cache_file)

    for path in paths:
        print(f"[INFO] Taranıyor: {path}", flush=True)
        text = github_raw(path)
        entries = parse_m3u(text, is_series=is_series)

        for key, val in entries.items():
            if key not in cache:
                cache[key] = {"imdb_id": None, "poster": None}

            imdb_id = cache[key].get("imdb_id")
            poster = cache[key].get("poster")

            # 1) JSON'da hem imdb_id hem poster varsa → hiç istek atma
            if imdb_id and poster:
                continue

            # 2) M3U'da tvg-id varsa ve JSON boşsa → imdb_id olarak kabul et
            if not imdb_id and val.get("imdb_id"):
                cache[key]["imdb_id"] = val["imdb_id"]
                imdb_id = val["imdb_id"]
                print(f"🎬 {key} → IMDb ID bulundu (M3U): {imdb_id}", flush=True)

            # 3) imdb_id varsa ama poster yoksa → poster çek
            if imdb_id and not poster:
                poster_from_title = fetch_title_poster(imdb_id)
                time.sleep(5)  # IMDb isteği sonrası bekle
                if poster_from_title:
                    cache[key]["poster"] = poster_from_title
                    print(f"🖼️ {key} → Poster bulundu: {poster_from_title}", flush=True)

            # 4) imdb_id yoksa → önce arama yap, sonra poster çek
            if not imdb_id:
                found_id = search_imdb_id_by_title(key)
                time.sleep(5)
                if found_id:
                    cache[key]["imdb_id"] = found_id
                    print(f"🎬 {key} → IMDb ID bulundu (search): {found_id}", flush=True)
                    poster_from_title = fetch_title_poster(found_id)
                    time.sleep(5)
                    if poster_from_title:
                        cache[key]["poster"] = poster_from_title
                        print(f"🖼️ {key} → Poster bulundu: {poster_from_title}", flush=True)

        save_cache(cache_file, cache)


if __name__ == "__main__":
    process_files(SERIES_PATHS, CACHE_SERIES, is_series=True)
    process_files(VOD_PATHS, CACHE_VOD, is_series=False)
