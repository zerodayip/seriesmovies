import os
import re
import json
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict

# --------- Ayarlar ---------
GH_TOKEN = os.getenv("GH_TOKEN")  # GitHub token
REPO = "zerodayip/m3u8file"
M3U_PATHS = [
    "dizigomdizi.m3u",
    "sezonlukdizi.m3u",
    "rec/recdizi.m3u"
]
OUT_DIR = "xtream"
CACHE_FILE = os.path.join(OUT_DIR, "imdb_series.json")
# ---------------------------

def github_raw(path: str) -> str:
    url = f"https://raw.githubusercontent.com/{REPO}/main/{path}"
    headers = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text

def parse_m3u(text: str):
    """M3U’dan unique (group-title, tvg-id) kombinasyonlarını alır"""
    entries = OrderedDict()
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
            group_match = re.search(r'group-title="([^"]*)"', line)
            imdb_id = tvg_id_match.group(1).strip() if tvg_id_match else ""
            group_title = group_match.group(1).strip() if group_match else "Bilinmeyen"
            key = (group_title, imdb_id)
            if key not in entries:
                entries[key] = True  # sadece unique key
    return list(entries.keys())

def get_imdb_poster(imdb_id, poster_cache):
    if imdb_id in poster_cache:
        return poster_cache[imdb_id]

    print(f"🌐 IMDb posteri için istek atılıyor: {imdb_id}", flush=True)
    imdb_url = f"https://www.imdb.com/title/{imdb_id}/"
    try:
        res = requests.get(imdb_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            poster_cache[imdb_id] = meta["content"]
            return meta["content"]
    except Exception as e:
        print(f"[HATA] {imdb_id}: IMDB posteri alınamadı: {e}", flush=True)

    poster_cache[imdb_id] = None
    return None

def search_imdb_by_name(series_name):
    query = requests.utils.quote(series_name)
    url = f"https://www.imdb.com/find?q={query}&s=tt&ttype=tv"
    try:
        print(f"🔎 IMDb araması yapılıyor: {series_name}", flush=True)
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        first_result = soup.select_one("li.find-result-item a")
        if first_result and 'href' in first_result.attrs:
            imdb_id = first_result['href'].split("/")[2]  # /title/ttXXXXXX/
            return imdb_id
    except Exception as e:
        print(f"[HATA] {series_name}: IMDb ID bulunamadı: {e}", flush=True)
    return None

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(data):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    cache = load_cache()
    poster_cache = {}

    for path in M3U_PATHS:
        print(f"[INFO] Taranıyor: {path}", flush=True)
        text = github_raw(path)
        entries = parse_m3u(text)

        for group_title, tvg_id in entries:
            # JSON’da zaten varsa ve aynı tvg-id ise skip
            if group_title in cache and cache[group_title].get("poster") and cache[group_title].get("imdb_id") == tvg_id:
                print(f"🗂️ JSON’dan poster alındı: {group_title}", flush=True)
                continue

            # JSON’da yoksa ekle
            if group_title not in cache:
                cache[group_title] = {"imdb_id": tvg_id, "poster": None}

            # IMDb ID eksikse arama
            if not cache[group_title].get("imdb_id") or cache[group_title]["imdb_id"] != tvg_id:
                found_imdb = tvg_id if tvg_id else search_imdb_by_name(group_title)
                if found_imdb:
                    cache[group_title]["imdb_id"] = found_imdb
                    print(f"✨ {group_title} [IMDb] → {found_imdb}", flush=True)

            # Poster yoksa çek
            if not cache[group_title].get("poster"):
                poster = get_imdb_poster(cache[group_title]["imdb_id"], poster_cache)
                if poster:
                    cache[group_title]["poster"] = poster
                    print(f"🖼️ {group_title} → Poster bulundu: {poster}", flush=True)

    # imdb_id boş olanlar en üstte, diğerleri alfabetik
    sorted_data = OrderedDict(
        sorted(cache.items(), key=lambda x: (0 if not x[1].get("imdb_id") else 1, x[0].lower()))
    )

    save_cache(sorted_data)
    print(f"✅ JSON kaydedildi: {CACHE_FILE}", flush=True)

if __name__ == "__main__":
    main()
