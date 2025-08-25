import os
import re
import json
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
import base64

GH_TOKEN = os.getenv("GH_TOKEN")
REPO = "zerodayip/m3u8file"
M3U_PATHS = [
    "dizigomdizi.m3u",
    "sezonlukdizi.m3u",
    "rec/recdizi.m3u"
]
OUT_DIR = "xtream"
CACHE_FILE = os.path.join(OUT_DIR, "imdb_series.json")

HEADERS = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}

def github_get_file(path):
    url = f"https://raw.githubusercontent.com/{REPO}/main/{path}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text

def github_get_file_sha(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()["sha"]

def github_update_file(path, content, message):
    sha = github_get_file_sha(path)
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "sha": sha
    }
    r = requests.put(url, headers=HEADERS, json=data, timeout=15)
    r.raise_for_status()
    print(f"✅ {path} güncellendi ve pushlandı.", flush=True)

def parse_m3u(text):
    entries = []
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
            group_match = re.search(r'group-title="([^"]*)"', line)
            series_name_match = re.search(r'tvg-name="([^"]*)"', line)
            imdb_id = tvg_id_match.group(1).strip() if tvg_id_match else ""
            group_title = group_match.group(1).strip() if group_match else "Bilinmeyen"
            series_name = series_name_match.group(1).strip() if series_name_match else group_title
            entries.append((line, series_name, group_title, imdb_id))
    return entries

def get_imdb_poster(imdb_id, poster_cache):
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

def search_imdb_by_name(series_name):
    query = requests.utils.quote(series_name)
    url = f"https://www.imdb.com/find?q={query}&s=tt&ttype=tv"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        first_result = soup.select_one("li.find-result-item a")
        if first_result and 'href' in first_result.attrs:
            imdb_id = first_result['href'].split("/")[2]
            print(f"✨ IMDb isteği yapıldı → {series_name}: {imdb_id}", flush=True)
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

def process_m3u(path, cache, poster_cache):
    text = github_get_file(path)
    entries = parse_m3u(text)
    new_lines = []

    for line, series_name, group_title, imdb_id in entries:
        # JSON’da yoksa ekle
        if series_name not in cache:
            cache[series_name] = {"imdb_id": imdb_id if imdb_id else None, "poster": None}

        # IMDb ID yoksa JSON veya arama ile al
        if not cache[series_name].get("imdb_id") and imdb_id:
            cache[series_name]["imdb_id"] = imdb_id
        elif not cache[series_name].get("imdb_id"):
            found_imdb = search_imdb_by_name(series_name)
            if found_imdb:
                cache[series_name]["imdb_id"] = found_imdb

        current_imdb_id = cache[series_name].get("imdb_id", "")
        poster_url = cache[series_name].get("poster")

        # Poster yoksa IMDb’den çek
        if current_imdb_id and not poster_url:
            poster = get_imdb_poster(current_imdb_id, poster_cache)
            if poster:
                cache[series_name]["poster"] = poster
                poster_url = poster

        # tvg-id veya tvg-logo güncelle
        new_line = line
        if current_imdb_id and 'tvg-id' not in line:
            new_line = re.sub(r'(#EXTINF:[^ ]*)', rf'\1 tvg-id="{current_imdb_id}"', new_line)
        if poster_url and 'tvg-logo' not in line:
            new_line = re.sub(r'(#EXTINF:[^"]*)', rf'\1 tvg-logo="{poster_url}"', new_line)

        new_lines.append(new_line)

    # Tek seferde birleştirip pushla → daha hızlı
    new_content = "\n".join(new_lines)
    github_update_file(path, new_content, f"📺 {path} güncellendi: poster ve tvg-id eklendi")

def main():
    cache = load_cache()
    poster_cache = {}

    for path in M3U_PATHS:
        print(f"[INFO] İşleniyor: {path}")
        process_m3u(path, cache, poster_cache)

    # imdb_id veya poster olmayanlar en üstte, diğerleri alfabetik
    sorted_data = OrderedDict(
        sorted(cache.items(), key=lambda x: (0 if not x[1].get("imdb_id") or not x[1].get("poster") else 1, x[0].lower()))
    )
    save_cache(sorted_data)
    print(f"✅ JSON kaydedildi: {CACHE_FILE}")

if __name__ == "__main__":
    main()
