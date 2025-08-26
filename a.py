import os
import re
import json
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
import base64
import time  # 5 saniye bekleme için

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
    url = f"https://raw.githubusercontent.com/{REPO}/main/{path}"
    headers = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def normalize_title(s: str) -> str:
    """Başlıkları IMDb arama eşleşmesinde güvenilir karşılaştırmak için normalize et."""
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
        else:
            name_match = re.search(r',(.+?)(?:\(|$)', line)
            key = name_match.group(1).strip() if name_match else "Bilinmeyen"

        entries[key] = {
            "imdb_id": tvg_id_match.group(1).strip() if tvg_id_match else None
        }
    return entries


def fetch_title_poster(imdb_id: str) -> str | None:
    """IMDb title sayfasından poster çeker."""
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
        time.sleep(5)  # 5 saniye bekleme
    return None


def search_imdb_id_by_title(title: str, is_series: bool = True) -> str | None:
    """IMDb arama sayfasından ID bulur."""
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
                href = a.get("href", "")
                m = re.search(r"/title/(tt\d+)/", href)
                if m:
                    return m.group(1)

        href = anchors[0].get("href", "")
        m = re.search(r"/title/(tt\d+)/", href)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"[HATA] IMDb araması başarısız ({title}): {e}", flush=True)
    finally:
        time.sleep(5)  # 5 saniye bekleme
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


def update_m3u_lines(m3u_text: str, cache: dict, is_series: bool = True) -> str:
    updated_lines = []
    for line in m3u_text.splitlines(keepends=True):
        if not line.startswith("#EXTINF"):
            updated_lines.append(line)
            continue

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


def push_to_github(path_in_repo: str, content: str, commit_message: str):
    url = f"https://api.github.com/repos/{REPO}/contents/{path_in_repo}"
    headers = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    sha = r.json()["sha"]
    data = {
        "message": commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "sha": sha
    }
    r = requests.put(url, headers=headers, json=data, timeout=TIMEOUT)
    r.raise_for_status()
    print(f"✅ GitHub'a push yapıldı: {path_in_repo}", flush=True)


def process_files(paths: list[str], cache_file: str, is_series: bool = True):
    cache = load_cache(cache_file)
    any_updated = False

    for path in paths:
        print(f"[INFO] Taranıyor: {path}", flush=True)
        text = github_raw(path)
        entries = parse_m3u(text, is_series=is_series)

        for key, val in entries.items():
            if key not in cache:
                cache[key] = {"imdb_id": None, "poster": None}

            imdb_id = cache[key].get("imdb_id")
            poster = cache[key].get("poster")
            updated_this = False

            if imdb_id and poster:
                continue

            if not imdb_id and val.get("imdb_id"):
                cache[key]["imdb_id"] = val["imdb_id"]
                imdb_id = val["imdb_id"]
                updated_this = True
                print(f"🎬 {key} → IMDb ID bulundu (M3U): {imdb_id}", flush=True)

            if imdb_id and not poster:
                poster_from_title = fetch_title_poster(imdb_id)
                if poster_from_title:
                    cache[key]["poster"] = poster_from_title
                    updated_this = True
                    print(f"🖼️ {key} → Poster bulundu (title): {poster_from_title}", flush=True)
                else:
                    print(f"❌ Poster bulunamadı (title) → {key} ({imdb_id})", flush=True)

            if not imdb_id:
                found_id = search_imdb_id_by_title(key, is_series=is_series)
                if found_id:
                    cache[key]["imdb_id"] = found_id
                    imdb_id = found_id
                    updated_this = True
                    print(f"🎬 {key} → IMDb ID bulundu (search): {found_id}", flush=True)

                    poster_from_title = fetch_title_poster(found_id)
                    if poster_from_title:
                        cache[key]["poster"] = poster_from_title
                        updated_this = True
                        print(f"🖼️ {key} → Poster bulundu (title): {poster_from_title}", flush=True)
                    else:
                        print(f"❌ Poster bulunamadı (title) → {key} ({found_id})", flush=True)
                else:
                    print(f"❌ IMDb sonucu bulunamadı (search) → {key}", flush=True)

            if updated_this:
                any_updated = True

    if any_updated:
        sorted_cache = OrderedDict(
            sorted(cache.items(), key=lambda x: (0 if not x[1].get("poster") else 1, x[0].lower()))
        )
        save_cache(sorted_cache, cache_file)
        print(f"✅ JSON kaydedildi: {cache_file}", flush=True)

        for path in paths:
            text = github_raw(path)
            updated_text = update_m3u_lines(text, sorted_cache, is_series=is_series)
            push_to_github(path, updated_text, f"Update posters & tvg-id for {path}")
    else:
        print("ℹ️ Güncellenecek yeni veri yok.", flush=True)


def main():
    process_files(SERIES_PATHS, CACHE_SERIES, is_series=True)
    process_files(VOD_PATHS, CACHE_VOD, is_series=False)


if __name__ == "__main__":
    main()
