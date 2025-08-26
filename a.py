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
    "dizigomfilmler.m3u",
    "setfilmizle.m3u",
    "rec/recfilm.m3u"
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


def parse_m3u(text: str, is_series=True):
    """Dizilerde group-title, filmlerde title kısmını alır"""
    entries = OrderedDict()
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)

            if is_series:
                group_match = re.search(r'group-title="([^"]*)"', line)
                key = group_match.group(1).strip() if group_match else "Bilinmeyen"
            else:
                name_match = re.search(r',(.+?)(?:\(|$)', line)
                key = name_match.group(1).strip() if name_match else "Bilinmeyen"

            entries[key] = {
                "imdb_id": tvg_id_match.group(1).strip() if tvg_id_match else None,
                "poster": None
            }
    return entries


def search_imdb_exact(title, is_series=True):
    """IMDb’de tam isim eşleşmeli arama yapar"""
    try:
        query = requests.utils.quote(title)
        ttype = "tv" if is_series else "ft"
        url = f"https://www.imdb.com/find?q={query}&s=tt&ttype={ttype}"
        print(f"🔎 IMDb araması: {title}", flush=True)
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        for li in soup.select("li.find-result-item"):
            a_tag = li.select_one("a")
            if a_tag:
                imdb_id = a_tag['href'].split("/")[2]
                name = a_tag.get_text(strip=True)

                if name.lower() == title.lower():  # tam eşleşme
                    img_tag = li.select_one("img")
                    poster = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
                    return imdb_id, poster
    except Exception as e:
        print(f"[HATA] IMDb araması {title}: {e}", flush=True)

    return None, None


def load_cache(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(data, path):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_m3u_lines(m3u_text, cache, is_series=True):
    updated_lines = []
    for line in m3u_text.splitlines(keepends=True):
        if line.startswith("#EXTINF"):
            key = None
            if is_series:
                group_match = re.search(r'group-title="([^"]*)"', line)
                key = group_match.group(1).strip() if group_match else None
            else:
                name_match = re.search(r',(.+?)(?:\(|$)', line)
                key = name_match.group(1).strip() if name_match else None

            if key and key in cache:
                data = cache[key]
                poster_url = data.get("poster")
                imdb_id = data.get("imdb_id")

                if poster_url:
                    if 'tvg-logo="' in line:
                        line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{poster_url}"', line)
                    else:
                        if is_series:
                            line = line.replace(" group-title=", f' tvg-logo="{poster_url}" group-title=')
                        else:
                            line = line.replace(",", f' tvg-logo="{poster_url}",')

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
    print(f"✅ GitHub'a push yapıldı: {path_in_repo}", flush=True)


def process_files(paths, cache_file, is_series=True):
    cache = load_cache(cache_file)
    updated = False

    for path in paths:
        print(f"[INFO] Taranıyor: {path}", flush=True)
        text = github_raw(path)
        entries = parse_m3u(text, is_series=is_series)

        for key, val in entries.items():
            if key not in cache:
                cache[key] = {"imdb_id": None, "poster": None}

            imdb_id = cache[key].get("imdb_id")
            poster = cache[key].get("poster")

            # M3U’dan gelen imdb_id yazılabilir
            if val["imdb_id"] and not imdb_id:
                cache[key]["imdb_id"] = val["imdb_id"]
                updated = True
                print(f"➕ {key} → IMDb ID bulundu (M3U): {val['imdb_id']}", flush=True)

            # IMDb’ye sadece eksik veri varsa istek at
            if not imdb_id or not poster:
                new_imdb_id, new_poster = search_imdb_exact(key, is_series)

                if new_imdb_id and not cache[key].get("imdb_id"):
                    cache[key]["imdb_id"] = new_imdb_id
                    updated = True
                    print(f"🎬 {key} → Yeni IMDb ID bulundu: {new_imdb_id}", flush=True)

                if new_poster and not cache[key].get("poster"):
                    cache[key]["poster"] = new_poster
                    updated = True
                    print(f"🖼️ {key} → Yeni poster bulundu: {new_poster}", flush=True)

    if updated:
        sorted_cache = OrderedDict(
            sorted(cache.items(), key=lambda x: (0 if not x[1].get("poster") else 1, x[0].lower()))
        )
        save_cache(sorted_cache, cache_file)
        print(f"✅ JSON kaydedildi: {cache_file}", flush=True)

        # M3U dosyalarını güncelle ve push
        for path in paths:
            text = github_raw(path)
            updated_text = update_m3u_lines(text, sorted_cache, is_series=is_series)
            push_to_github(path, updated_text, f"Update posters & tvg-id for {path}")
    else:
        print("ℹ️ Güncellenecek yeni veri bulunamadı.", flush=True)


def main():
    process_files(SERIES_PATHS, CACHE_SERIES, is_series=True)
    process_files(VOD_PATHS, CACHE_VOD, is_series=False)


if __name__ == "__main__":
    main()
