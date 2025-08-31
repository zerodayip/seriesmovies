import os
import re
import json
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
import time  # 5 saniye bekleme için

# --------- Ayarlar ---------
GH_TOKEN = os.getenv("GH_TOKEN")
if not GH_TOKEN:
    raise Exception("❌ GH_TOKEN bulunamadı! Özel repo için zorunlu.")

REPO = "zerodayip/m3u8file"

SERIES_PATHS = [
    "dizigomdizi.m3u",
    "sezonlukdizi.m3u",
    "rec/recdizi.m3u"
]
VOD_PATHS = [
    "dizigomfilmler.m3u",
    "setfilmizlefilmler.m3u",
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
    url = f"https://raw.githubusercontent.com/{REPO}/main/{path}"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def normalize_title(s: str) -> str:
    if not s:
        return ""
    table = str.maketrans({
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "…": "...",
        "＆": "&",
        "：": ":",
    })
    s = s.translate(table)
    s = re.sub(r"\s+", " ", s).strip()
    return s.casefold()


def parse_m3u(text: str, is_series=True):
    entries = OrderedDict()
    for line in text.splitlines():
        if not line.startswith("#EXTINF"):
            continue

        tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)

        if is_series:
            group_match = re.search(r'group-title="([^"]*)"', line)
            key = group_match.group(1).strip() if group_match else "Bilinmeyen"
            entries[key] = {
                "imdb_id": tvg_id_match.group(1).strip() if tvg_id_match else None
            }
        else:
            name_match = re.search(r',(.+?)(?:\(|$)', line)
            key = name_match.group(1).strip() if name_match else "Bilinmeyen"

            # 🎬 yıl bilgisini sadece group-title’dan al
            group_match = re.search(r'group-title="([^"]*)"', line)
            year = None
            if group_match:
                m = re.search(r'(\d{4})', group_match.group(1))
                if m:
                    year = m.group(1)

            entries[key] = {
                "imdb_id": tvg_id_match.group(1).strip() if tvg_id_match else None,
                "year": year
            }
    return entries


def fetch_title_poster(imdb_id: str) -> str | None:
    if not imdb_id:
        return None
    url = f"https://www.imdb.com/title/{imdb_id}/"
    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        og = soup.find("meta", attrs={"property": "og:image"})
        if og and og.get("content"):
            return og["content"]
    except Exception as e:
        print(f"[HATA] Poster alınamadı ({imdb_id}): {e}", flush=True)
    finally:
        time.sleep(5)
    return None


def search_imdb_id_by_title(title: str, is_series: bool = True) -> str | None:
    try:
        q = requests.utils.quote(title)
        ttype = "tv" if is_series else "ft"
        url = f"https://www.imdb.com/find?q={q}&s=tt&ttype={ttype}"
        print(f"🔎 IMDb araması: {title}", flush=True)
        r = requests.get(url, headers=HTTP_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        anchors = soup.select("li.find-title-result a.ipc-metadata-list-summary-item__t")
        if not anchors:
            anchors = soup.select("li.find-result-item a")
        if not anchors:
            return None

        norm_query = normalize_title(title)
        for a in anchors:
            text = a.get_text(strip=True)
            if normalize_title(text) == norm_query:
                m = re.search(r"/title/(tt\d+)/", a.get("href", ""))
                if m:
                    return m.group(1)

        m = re.search(r"/title/(tt\d+)/", anchors[0].get("href", ""))
        if m:
            return m.group(1)
    except Exception as e:
        print(f"[HATA] IMDb araması başarısız ({title}): {e}", flush=True)
    finally:
        time.sleep(5)
    return None


def load_cache(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(data: dict, path: str):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def process_files(paths: list[str], cache_file: str, is_series: bool = True):
    cache = load_cache(cache_file)
    group_cache = {} if is_series else None

    for path in paths:
        print(f"[INFO] Taranıyor: {path}", flush=True)
        text = github_raw(path)
        entries = parse_m3u(text, is_series=is_series)

        for key, val in entries.items():
            if is_series and key in group_cache:
                cache[key] = group_cache[key]
                continue

            if key not in cache:
                cache[key] = {"imdb_id": None, "poster": None}

            imdb_id = cache[key].get("imdb_id")
            poster = cache[key].get("poster")

            if imdb_id and poster:
                if is_series:
                    group_cache[key] = cache[key]
                continue

            if not imdb_id and val.get("imdb_id"):
                cache[key]["imdb_id"] = val["imdb_id"]
                imdb_id = val["imdb_id"]
                print(f"🎬 {key} → IMDb ID bulundu (M3U): {imdb_id}", flush=True)

            if imdb_id and not poster:
                poster_from_title = fetch_title_poster(imdb_id)
                if poster_from_title:
                    cache[key]["poster"] = poster_from_title
                    print(f"🖼️ {key} → Poster bulundu: {poster_from_title}", flush=True)

            if not imdb_id:
                found_id = search_imdb_id_by_title(key, is_series=is_series)
                if found_id:
                    cache[key]["imdb_id"] = found_id
                    imdb_id = found_id
                    print(f"🎬 {key} → IMDb ID bulundu (search): {found_id}", flush=True)

                    poster_from_title = fetch_title_poster(found_id)
                    if poster_from_title:
                        cache[key]["poster"] = poster_from_title
                        print(f"🖼️ {key} → Poster bulundu: {poster_from_title}", flush=True)

            if is_series:
                group_cache[key] = cache[key]

    save_cache(cache, cache_file)
    print(f"✅ JSON kaydedildi: {cache_file}", flush=True)


def process_vod_files(paths: list[str], cache_file: str):
    cache = load_cache(cache_file)

    for path in paths:
        print(f"[INFO] Taranıyor: {path}", flush=True)
        text = github_raw(path)
        entries = parse_m3u(text, is_series=False)

        for key, val in entries.items():
            if key not in cache:
                cache[key] = {"imdb_id": None, "poster": None, "year": None}

            imdb_id = cache[key].get("imdb_id")
            poster = cache[key].get("poster")

            if val.get("year"):
                cache[key]["year"] = val["year"]

            if imdb_id and poster:
                continue

            if not imdb_id and val.get("imdb_id"):
                cache[key]["imdb_id"] = val["imdb_id"]
                imdb_id = val["imdb_id"]
                print(f"🎬 {key} → IMDb ID bulundu (M3U): {imdb_id}", flush=True)

            if imdb_id and not poster:
                poster_from_title = fetch_title_poster(imdb_id)
                if poster_from_title:
                    cache[key]["poster"] = poster_from_title
                    print(f"🖼️ {key} → Poster bulundu: {poster_from_title}", flush=True)

            if not imdb_id:
                found_id = search_imdb_id_by_title(key, is_series=False)
                if found_id:
                    cache[key]["imdb_id"] = found_id
                    imdb_id = found_id
                    print(f"🎬 {key} → IMDb ID bulundu (search): {found_id}", flush=True)

                    poster_from_title = fetch_title_poster(found_id)
                    if poster_from_title:
                        cache[key]["poster"] = poster_from_title
                        print(f"🖼️ {key} → Poster bulundu: {poster_from_title}", flush=True)

    save_cache(cache, cache_file)
    print(f"✅ JSON kaydedildi: {cache_file}", flush=True)


def main():
    process_files(SERIES_PATHS, CACHE_SERIES, is_series=True)
    process_vod_files(VOD_PATHS, CACHE_VOD)


if __name__ == "__main__":
    main()
