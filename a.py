import os
import re
import json

# --------- Ayarlar ---------
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
# ---------------------------

def load_cache(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def update_m3u_file(path: str, cache: dict, is_series=True):
    if not os.path.exists(path):
        print(f"[UYARI] Dosya bulunamadı: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = []
    for line in lines:
        if line.startswith("#EXTINF"):
            key = None
            if is_series:
                match = re.search(r'group-title="([^"]*)"', line)
                key = match.group(1).strip() if match else "Bilinmeyen"
            else:
                match = re.search(r',(.+?)(?:\(|$)', line)
                key = match.group(1).strip() if match else "Bilinmeyen"

            if key and key in cache:
                imdb_id = cache[key].get("imdb_id") or ""
                poster = cache[key].get("poster") or ""

                # tvg-id güncelle
                if 'tvg-id="' in line:
                    line = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{imdb_id}"', line)
                else:
                    line = line.replace("#EXTINF:", f'#EXTINF:tvg-id="{imdb_id}",')

                # tvg-logo güncelle
                if 'tvg-logo="' in line:
                    line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{poster}"', line)
                else:
                    parts = line.split(' ', 1)
                    line = f'{parts[0]} tvg-logo="{poster}" ' + (parts[1] if len(parts) > 1 else '')

        updated_lines.append(line)

    # Orijinal dosyanın üzerine yaz
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print(f"[GÜNCELLENDİ] {path}")

def main():
    series_cache = load_cache(CACHE_SERIES)
    vod_cache = load_cache(CACHE_VOD)

    for path in SERIES_PATHS:
        update_m3u_file(path, series_cache, is_series=True)

    for path in VOD_PATHS:
        update_m3u_file(path, vod_cache, is_series=False)

if __name__ == "__main__":
    main()
