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

SERIES_PATHS = [
    "dizigomdizi.m3u",
    "sezonlukdizi.m3u",
    "rec/recdizi.m3u"
]
MOVIE_PATHS = [
    "dizigomfimler.m3u",
    "rec/recfilm.m3u"
]

OUT_DIR = "xtream"
CACHE_SERIES = os.path.join(OUT_DIR, "imdb_series.json")
CACHE_MOVIES = os.path.join(OUT_DIR, "imdb_vod.json")
MAX_WORKERS = 12
# ---------------------------

def github_raw(path: str) -> str:
    url = f"https://raw.githubusercontent.com/{REPO}/main/{path}"
    headers = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text

def parse_series_m3u(text: str):
    """Dizi M3U -> (group_title, imdb_id)"""
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

def parse_movies_m3u(text: str):
    """Film M3U -> (film_adi, imdb_id)"""
    entries = OrderedDict()
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
            name_match = re.search(r',(.*?)(?:\s*\(.*)?$', line)
            imdb_id = tvg_id_match.group(1).strip() if tvg_id_match else ""
            name = name_match.group(1).strip() if name_match else "Bilinmeyen"
            key = (name, imdb_id)
            if key not in entries:
                entries[key] = True
    return list(entries.keys())

def get_imdb_poster(imdb_id):
    try:
        res = requests.get(f"https://www.imdb.com/title/{imdb_id}/", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            return meta["content"]
    except:
        pass
    return None

def search_imdb_by_name(name, ttype="tv"):
    try:
        query = requests.utils.quote(name)
        res = requests.get(f"https://www.imdb.com/find?q={query}&s=tt&ttype={ttype}",
                           headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        first_result = soup.select_one("li.find-result-item a")
        if first_result and 'href' in first_result.attrs:
            imdb_id = first_result['href'].split("/")[2]
            return name, imdb_id
    except:
        pass
    return name, None

def load_cache(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(file_path, data):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_m3u_lines(m3u_text, json_cache):
    updated_lines = []
    for line in m3u_text.splitlines(keepends=True):
        if line.startswith("#EXTINF"):
            key_match = re.search(r'group-title="([^"]*)"', line)
            name_match = re.search(r',(.*?)(?:\s*\(.*)?$', line)

            key = None
            if key_match and key_match.group(1) in json_cache:
                key = key_match.group(1)  # dizi için group-title
            elif name_match and name_match.group(1).strip() in json_cache:
                key = name_match.group(1).strip()  # film için isim

            if key and key in json_cache:
                data = json_cache[key]
                poster_url = data.get("poster")
                imdb_id = data.get("imdb_id")

                if poster_url:
                    if 'tvg-logo="' in line:
                        line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{poster_url}"', line)
                    else:
                        line = line.replace(" group-title=", f' tvg-logo="{poster_url}" group-title=')

                if imdb_id:
                    if 'tvg-id="' in line:
                        line = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{imdb_id}"', line)
                    else:
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
    print(f"✅ GitHub'a push yapıldı: {path_in_repo}")

def process_files(paths, cache_file, parser, ttype):
    cache = load_cache(cache_file)
    tasks = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for path in paths:
            text = github_raw(path)
            entries = parser(text)

            for key, imdb_id in entries:
                if key not in cache:
                    cache[key] = {"imdb_id": imdb_id if imdb_id else None, "poster": None}

                if not cache[key].get("imdb_id"):
                    tasks.append(executor.submit(search_imdb_by_name, key, ttype))

                if cache[key].get("imdb_id") and not cache[key].get("poster"):
                    tasks.append(executor.submit(lambda k, id: (k, get_imdb_poster(id)), key, cache[key]["imdb_id"]))

        for future in as_completed(tasks):
            res = future.result()
            if isinstance(res, tuple):
                key, value = res
                if key in cache and value:
                    if value.startswith("http"):
                        cache[key]["poster"] = value
                    elif value.startswith("tt"):
                        cache[key]["imdb_id"] = value

    for path in paths:
        text = github_raw(path)
        updated_text = update_m3u_lines(text, cache)
        push_to_github(path, updated_text, f"Update posters & tvg-id for {path}")

    sorted_data = OrderedDict(
        sorted(cache.items(), key=lambda x: (0 if not x[1].get("imdb_id") else 1, x[0].lower()))
    )
    save_cache(cache_file, sorted_data)

def main():
    process_files(SERIES_PATHS, CACHE_SERIES, parse_series_m3u, "tv")
    process_files(MOVIE_PATHS, CACHE_MOVIES, parse_movies_m3u, "ft")  # ft = film type

if __name__ == "__main__":
    main()
