import os
import re
import json
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
import base64

# --------- Ayarlar ---------
GH_TOKEN = os.getenv("GH_TOKEN")
REPO = "zerodayip/m3u8file"

SERIES_PATHS = [
    "dizigomdizi.m3u",
    "sezonlukdizi.m3u",
    "rec/recdizi.m3u"
]
VOD_PATHS = [
    "dizigomfilmler.m3u"
]

OUT_DIR = "xtream"
CACHE_SERIES = os.path.join(OUT_DIR, "imdb_series.json")
CACHE_VOD = os.path.join(OUT_DIR, "imdb_vod.json")
# ---------------------------

def github_raw(path: str) -> str:
    url = f"https://raw.githubusercontent.com/{REPO}/main/{path}"
    headers = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text

def parse_m3u_series(text: str):
    entries = OrderedDict()
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
            group_match = re.search(r'group-title="([^"]*)"', line)
            imdb_id = tvg_id_match.group(1).strip() if tvg_id_match else None
            group_title = group_match.group(1).strip() if group_match else "Bilinmeyen"
            entries[group_title] = imdb_id
    return entries

def parse_m3u_vod(text: str):
    entries = OrderedDict()
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
            name_match = re.search(r',(.+)$', line)
            imdb_id = tvg_id_match.group(1).strip() if tvg_id_match else None
            if name_match:
                raw_title = name_match.group(1).strip()
                # Parantez içini çıkar
                title = re.sub(r'\s*\(.*?\)\s*', '', raw_title)
            else:
                title = "Bilinmeyen"
            entries[title] = imdb_id
    return entries

def get_imdb_poster(imdb_id):
    try:
        print(f"🌐 IMDb posteri için istek atılıyor: {imdb_id}", flush=True)
        res = requests.get(f"https://www.imdb.com/title/{imdb_id}/", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            return meta["content"]
    except Exception as e:
        print(f"[HATA] {imdb_id}: {e}", flush=True)
    return None

def search_imdb_by_name(title, is_series=True):
    try:
        print(f"🔎 IMDb araması yapılıyor: {title}", flush=True)
        query = requests.utils.quote(title)
        ttype = "tv" if is_series else "ft"
        res = requests.get(f"https://www.imdb.com/find?q={query}&s=tt&ttype={ttype}",
                           headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        first_result = soup.select_one("li.find-result-item a")
        if first_result and 'href' in first_result.attrs:
            imdb_id = first_result['href'].split("/")[2]
            return imdb_id
    except Exception as e:
        print(f"[HATA] {title}: {e}", flush=True)
    return None

def load_cache(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(data, path):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_m3u_lines(text, cache, is_series=True):
    updated_lines = []
    for line in text.splitlines(keepends=True):
        if line.startswith("#EXTINF"):
            key = None
            if is_series:
                group_match = re.search(r'group-title="([^"]*)"', line)
                key = group_match.group(1).strip() if group_match else None
            else:
                name_match = re.search(r',(.+)$', line)
                if name_match:
                    raw_title = name_match.group(1).strip()
                    key = re.sub(r'\s*\(.*?\)\s*', '', raw_title)

            if key and key in cache:
                data = cache[key]
                poster = data.get("poster")
                imdb_id = data.get("imdb_id")

                if poster:
                    if 'tvg-logo="' in line:
                        line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{poster}"', line)
                    else:
                        if is_series:
                            line = line.replace(" group-title=", f' tvg-logo="{poster}" group-title=')
                        else:
                            line = line.replace(",", f' tvg-logo="{poster}",', 1)

                if imdb_id:
                    if 'tvg-id="' in line:
                        line = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{imdb_id}"', line)
                    else:
                        line = line.replace("#EXTINF:", f'#EXTINF:-1 tvg-id="{imdb_id}"', 1)
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

def process_files(paths, cache_file, is_series=True):
    cache = load_cache(cache_file)

    for path in paths:
        print(f"[INFO] Taranıyor: {path}", flush=True)
        text = github_raw(path)
        entries = parse_m3u_series(text) if is_series else parse_m3u_vod(text)

        # Cache güncelle
        for key, tvg_id in entries.items():
            if key not in cache:
                cache[key] = {"imdb_id": tvg_id, "poster": None}

            # IMDb ID yoksa ara
            if not cache[key].get("imdb_id"):
                imdb_id = search_imdb_by_name(key, is_series)
                if imdb_id:
                    cache[key]["imdb_id"] = imdb_id
                    print(f"✨ {key} [IMDb] → {imdb_id}", flush=True)

            # Poster yoksa çek
            if cache[key].get("imdb_id") and not cache[key].get("poster"):
                poster = get_imdb_poster(cache[key]["imdb_id"])
                if poster:
                    cache[key]["poster"] = poster
                    print(f"🖼️ {key} → Poster bulundu", flush=True)

        # M3U güncelle
        updated_text = update_m3u_lines(text, cache, is_series)
        push_to_github(path, updated_text, f"Update posters & tvg-id for {path}")

    # TVG-ID veya poster olmayanları üste alacak şekilde sırala
    sorted_cache = OrderedDict(sorted(
        cache.items(),
        key=lambda x: (1 if x[1].get("imdb_id") and x[1].get("poster") else 0, x[0].lower())
    ))
    save_cache(sorted_cache, cache_file)
    print(f"✅ JSON kaydedildi: {cache_file}", flush=True)

def main():
    process_files(SERIES_PATHS, CACHE_SERIES, is_series=True)
    process_files(VOD_PATHS, CACHE_VOD, is_series=False)

if __name__ == "__main__":
    main()
