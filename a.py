import os
import re
import json
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict

# --------- Ayarlar ---------
GH_TOKEN = os.getenv("GH_TOKEN")  # GH_TOKEN ortam değişkeninden alınır
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
    """GH_TOKEN ile private repo'dan raw m3u içeriği çek."""
    url = f"https://raw.githubusercontent.com/{REPO}/main/{path}"
    headers = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text

def parse_m3u(text: str):
    """M3U satırlarını tvg-id ve group-title bazlı ayıkla."""
    entries = []
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
            group_match = re.search(r'group-title="([^"]*)"', line)
            imdb_id = tvg_id_match.group(1).strip() if tvg_id_match else ""
            group_title = group_match.group(1).strip() if group_match else "Bilinmeyen"
            entries.append((group_title, imdb_id))
    return entries

def get_imdb_poster(imdb_id, poster_cache):
    """IMDb sayfasından poster URL çek (scrape)."""
    if imdb_id in poster_cache:
        return poster_cache[imdb_id]

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
    new_data = {}

    for path in M3U_PATHS:
        print(f"[INFO] Taranıyor: {path}")
        text = github_raw(path)
        entries = parse_m3u(text)

        for series_name, imdb_id in entries:
            if series_name not in cache:
                cache[series_name] = {"imdb_id": imdb_id, "poster": None}

            # imdb_id güncellendi mi?
            if not cache[series_name].get("imdb_id") and imdb_id:
                cache[series_name]["imdb_id"] = imdb_id

            # poster otomatik çekme
            imdb_id = cache[series_name].get("imdb_id", "")
            if imdb_id and not cache[series_name].get("poster"):
                poster = get_imdb_poster(imdb_id, poster_cache)
                if poster:
                    cache[series_name]["poster"] = poster
                    print(f"[POSTER] {series_name} → {poster}")

    # imdb_id olmayanlar en üstte olacak şekilde sıralama
    sorted_data = OrderedDict(
        sorted(cache.items(), key=lambda x: (0 if not x[1].get("imdb_id") else 1, x[0].lower()))
    )

    save_cache(sorted_data)
    print(f"✅ JSON kaydedildi: {CACHE_FILE}")

if __name__ == "__main__":
    main()
