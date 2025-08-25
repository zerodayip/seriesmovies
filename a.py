import os
import re
import json
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

# --------- Ayarlar ---------
GH_TOKEN = os.getenv("GH_TOKEN")
REPO = "zerodayip/m3u8file"
M3U_PATHS = [
    "dizigomdizi.m3u",
    "sezonlukdizi.m3u",
    "rec/recdizi.m3u"
]
OUT_DIR = "xtream"
CACHE_FILE = os.path.join(OUT_DIR, "imdb_series.json")
MAX_WORKERS = 10  # Paralel HTTP thread sayısı
# ---------------------------

def github_raw(path: str) -> str:
    url = f"https://raw.githubusercontent.com/{REPO}/main/{path}"
    headers = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text

def parse_m3u(text: str):
    entries = OrderedDict()
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
            group_match = re.search(r'group-title="([^"]*)"', line)
            imdb_id = tvg_id_match.group(1).strip() if tvg_id_match else ""
            group_title = group_match.group(1).strip() if group_match else "Bilinmeyen"
            key = (group_title, imdb_id)
            if key not in entries:
                entries[key] = True
    return list(entries.keys())

def get_imdb_poster(imdb_id):
    """Paralel çalışacak poster çekme fonksiyonu"""
    try:
        print(f"🌐 IMDb posteri için istek atılıyor: {imdb_id}", flush=True)
        res = requests.get(f"https://www.imdb.com/title/{imdb_id}/", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            return imdb_id, meta["content"]
    except Exception as e:
        print(f"[HATA] {imdb_id}: {e}", flush=True)
    return imdb_id, None

def search_imdb_by_name(series_name):
    try:
        print(f"🔎 IMDb araması yapılıyor: {series_name}", flush=True)
        query = requests.utils.quote(series_name)
        res = requests.get(f"https://www.imdb.com/find?q={query}&s=tt&ttype=tv",
                           headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        first_result = soup.select_one("li.find-result-item a")
        if first_result and 'href' in first_result.attrs:
            imdb_id = first_result['href'].split("/")[2]
            return series_name, imdb_id
    except Exception as e:
        print(f"[HATA] {series_name}: {e}", flush=True)
    return series_name, None

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(data):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_m3u_lines(m3u_text, json_cache):
    updated_lines = []
    for line in m3u_text.splitlines(keepends=True):
        if line.startswith("#EXTINF"):
            group_match = re.search(r'group-title="([^"]*)"', line)
            if group_match:
                group_title = group_match.group(1).strip()
                if group_title in json_cache:
                    data = json_cache[group_title]
                    poster_url = data.get("poster")
                    imdb_id = data.get("imdb_id")
                    if poster_url:
                        if 'tvg-logo="' in line:
                            line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{poster_url}"', line)
                        else:
                            line = line.replace(" group-title=", f' tvg-logo="{poster_url}" group-title=')
                    if imdb_id and 'tvg-id="' not in line:
                        line = line.replace("#EXTINF:", f'#EXTINF:-1 tvg-id="{imdb_id}" ', 1)
        updated_lines.append(line)
    return ''.join(updated_lines)

def push_to_github(path_in_repo, content, commit_message):
    url = f"https://api.github.com/repos/{REPO}/contents/{path_in_repo}"
    headers = {"Authorization": f"Bearer {GH_TOKEN}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    sha = r.json()["sha"]
    data = {
        "message": commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "sha": sha
    }
    r = requests.put(url, headers=headers, json=data)
    r.raise_for_status()
    print(f"✅ GitHub'a push yapıldı: {path_in_repo}", flush=True)

def main():
    cache = load_cache()

    # --- IMDb ID ve posterleri paralel çek ---
    tasks = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for path in M3U_PATHS:
            print(f"[INFO] Taranıyor: {path}", flush=True)
            text = github_raw(path)
            entries = parse_m3u(text)

            for group_title, tvg_id in entries:
                # Skip JSON’da poster ve imdb_id varsa
                if group_title in cache and cache[group_title].get("poster") and cache[group_title].get("imdb_id"):
                    print(f"🗂️ JSON’dan poster alındı: {group_title}", flush=True)
                    continue
                if group_title not in cache:
                    cache[group_title] = {"imdb_id": tvg_id if tvg_id else None, "poster": None}

                # IMDb ID yoksa arama
                if not cache[group_title].get("imdb_id"):
                    tasks.append(executor.submit(search_imdb_by_name, group_title))
                else:
                    tasks.append(executor.submit(get_imdb_poster, cache[group_title]["imdb_id"]))

        # Sonuçları bekle ve cache güncelle
        for future in as_completed(tasks):
            res = future.result()
            if isinstance(res, tuple):
                key, value = res
                if key in cache and "search" not in str(res):
                    # Poster sonucu
                    cache[key]["poster"] = value
                    if value:
                        print(f"🖼️ {key} → Poster bulundu: {value}", flush=True)
                else:
                    # Arama sonucu
                    if value:
                        cache[key]["imdb_id"] = value
                        print(f"✨ {key} [IMDb] → {value}", flush=True)

    # --- M3U güncelle ve push ---
    for path in M3U_PATHS:
        text = github_raw(path)
        updated_text = update_m3u_lines(text, cache)
        push_to_github(path, updated_text, f"Update posters & tvg-id for {path}")

    # --- Cache kaydet ---
    sorted_data = OrderedDict(
        sorted(cache.items(), key=lambda x: (0 if not x[1].get("imdb_id") else 1, x[0].lower()))
    )
    save_cache(sorted_data)
    print(f"✅ JSON kaydedildi: {CACHE_FILE}", flush=True)

if __name__ == "__main__":
    main()
