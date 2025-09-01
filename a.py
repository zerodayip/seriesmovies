import os
import re
import json
import requests

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

CACHE_SERIES = "xtream/imdb_series.json"
CACHE_VOD = "xtream/imdb_vod.json"

TIMEOUT = 15
# ---------------------------


def github_raw(path: str) -> str:
    """Repo içinden dosya içeriğini al"""
    url = f"https://raw.githubusercontent.com/{REPO}/main/{path}"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def load_json(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def normalize_title(s: str) -> str:
    """İsimleri karşılaştırma için normalize et"""
    if not s:
        return ""
    return re.sub(r"[^A-Z0-9]+", " ", s.upper()).strip()


def extract_year_from_group(line: str) -> str | None:
    """group-title içinden yıl çıkar (örn: '2025 FİLMLERİ' → '2025')"""
    m = re.search(r'group-title="([^"]*)"', line)
    if not m:
        return None
    txt = m.group(1)
    ym = re.search(r"(\d{4})", txt)
    return ym.group(1) if ym else None


def update_m3u(text: str, cache: dict, is_series=True) -> str:
    """M3U içeriğini JSON cache'e göre güncelle"""
    new_lines = []
    for line in text.splitlines():
        if line.startswith("#EXTINF"):
            updated_line = line
            entry = None

            if is_series:
                # Diziler: group-title bazlı eşleşme
                group_match = re.search(r'group-title="([^"]*)"', line)
                key = group_match.group(1).strip() if group_match else None
                entry = cache.get(key)
            else:
                # Filmler: ad + yıl ZORUNLU eşleşme
                name_match = re.search(r',(.+?)(?:\(|$)', line)
                film_name = name_match.group(1).strip() if name_match else None
                film_year = extract_year_from_group(line)

                if film_name and film_year:
                    norm_name = normalize_title(film_name)
                    for k, v in cache.items():
                        if normalize_title(k) == norm_name and v.get("year") == film_year:
                            entry = v
                            break

            if entry:
                imdb_id = entry.get("imdb_id")
                poster = entry.get("poster")

                if imdb_id:
                    if re.search(r'tvg-id="[^"]*"', updated_line):
                        updated_line = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{imdb_id}"', updated_line)
                    else:
                        updated_line = updated_line.replace("#EXTINF", f'#EXTINF tvg-id="{imdb_id}"', 1)

                if poster:
                    if re.search(r'tvg-logo="[^"]*"', updated_line):
                        updated_line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{poster}"', updated_line)
                    else:
                        updated_line = updated_line.replace("#EXTINF", f'#EXTINF tvg-logo="{poster}"', 1)

            new_lines.append(updated_line)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def process_files(paths: list[str], cache_file: str, is_series=True):
    cache = load_json(cache_file)

    for path in paths:
        print(f"[INFO] Güncelleniyor: {path}", flush=True)
        text = github_raw(path)
        updated = update_m3u(text, cache, is_series=is_series)

        # Aynı isimle kaydet
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"✅ Kaydedildi: {path}", flush=True)


def main():
    process_files(SERIES_PATHS, CACHE_SERIES, is_series=True)
    process_files(VOD_PATHS, CACHE_VOD, is_series=False)


if __name__ == "__main__":
    main()
