import re
import json
from collections import defaultdict

def parse_m3u_text_to_json(text):
    lines = text.splitlines()
    channels = {}
    categories = {}
    category_name_to_id = {}
    category_counter = 1
    def get_category_id(name):
        nonlocal category_counter
        if name not in category_name_to_id:
            category_name_to_id[name] = str(category_counter)
            category_counter += 1
        return category_name_to_id[name]

    id_counter = 1000
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF"):
            name_match = re.search(r',(.+)$', line)
            logo_match = re.search(r'tvg-logo="(.*?)"', line)
            group_match = re.search(r'group-title="(.*?)"', line)
            title = name_match.group(1).strip() if name_match else f"Channel {id_counter}"
            icon = logo_match.group(1) if logo_match else ""
            group = group_match.group(1) if group_match else "Uncategorized"
            category_id = get_category_id(group)
            categories[category_id] = group
            stream_url = lines[i + 1].strip() if (i + 1) < len(lines) else ""
            if stream_url.startswith("http"):
                channels[str(id_counter)] = {
                    "name": title,
                    "icon": icon,
                    "url": stream_url,
                    "category_id": category_id
                }
                id_counter += 1
        i += 1
    return {"channels": channels, "categories": categories}

def parse_series(text):
    lines = text.splitlines()
    series = {}
    categories = {}
    category_name_to_id = {}
    category_counter = 1

    def get_category_id(name):
        nonlocal category_counter
        if name not in category_name_to_id:
            category_name_to_id[name] = str(category_counter)
            category_counter += 1
        return category_name_to_id[name]

    id_counter = 3000
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("#EXTINF"):
            i += 1
            continue
        info = line
        url = lines[i + 1].strip() if (i + 1) < len(lines) else ""
        if not url.startswith("http"):
            i += 1
            continue

        name_match = re.search(r'tvg-name="(.*?)"', info)
        logo_match = re.search(r'tvg-logo="(.*?)"', info)
        group_match = re.search(r'group-title="(.*?)"', info)
        full_name = name_match.group(1) if name_match else ""
        logo = logo_match.group(1) if logo_match else ""
        group = group_match.group(1) if group_match else "Diziler"

        extinf_desc_match = re.search(r',(.+)$', info)
        episode_lang = ""
        if extinf_desc_match:
            desc = extinf_desc_match.group(1).upper()
            if "ALTYAZI" in desc:
                episode_lang = "TÜRKÇE ALTYAZI"
            elif "DUBLAJ" in desc:
                episode_lang = "TÜRKÇE DUBLAJ"

        match = re.match(r'^(.*?)\s+S(\d+)E(\d+)', full_name, re.I)
        if not match:
            i += 1
            continue
        raw_show_name = match.group(1).strip()
        season = match.group(2).zfill(2)
        episode = match.group(3).zfill(2)
        show_name = f"{raw_show_name} {episode_lang}" if episode_lang else raw_show_name

        category_id = get_category_id(group)
        categories[category_id] = group

        # Diziyi bul veya oluştur
        found_id = None
        for k, v in series.items():
            if v["name"] == show_name:
                found_id = k
                break
        if not found_id:
            found_id = str(id_counter)
            series[found_id] = {
                "series_id": found_id,
                "name": show_name,
                "icon": logo,
                "cover": logo,
                "cover_big": logo,
                "plot": "",
                "cast": "",
                "director": "",
                "genre": "",
                "releaseDate": "",
                "rating": "",
                "rating_5based": 0,
                "episode_run_time": "60",
                "youtube_trailer": "",
                "backdrop_path": logo,
                "category_id": category_id,
                "last_modified": "",
                "seasons": {},
                "episodes": {}
            }
            id_counter += 1

        # Seasons
        if season not in series[found_id]["seasons"]:
            series[found_id]["seasons"][season] = {}
        series[found_id]["seasons"][season][episode] = {
            "title": f"Bölüm {int(episode)}",
            "url": url
        }

        # Episodes
        if season not in series[found_id]["episodes"]:
            series[found_id]["episodes"][season] = []
        series[found_id]["episodes"][season].append({
            "id": f"{found_id}_{season}_{episode}",
            "episode_num": int(episode),
            "title": f"Bölüm {int(episode)}",
            "name": f"Bölüm {int(episode)}",
            "container_extension": (
                "m3u8" if url.endswith(".m3u8") else
                "ts" if url.endswith(".ts") else
                "mp4" if url.endswith(".mp4") else
                "mkv" if url.endswith(".mkv") else
                "mp4"
            ),
            "info": {"language": episode_lang},
            "season": season,
            "url": url,
            "added": ""
        })
        i += 2
    return {"series": series, "categories": categories}

# Dosyaları oku, JSON'a çevir, kaydet
def main():
    with open("vavoo.m3u", encoding="utf-8") as f:
        live_m3u = f.read()
    with open("recfilm.m3u", encoding="utf-8") as f:
        vod_m3u = f.read()
    with open("sezonlukdizi.m3u", encoding="utf-8") as f:
        series_m3u = f.read()

    live_json = parse_m3u_text_to_json(live_m3u)
    vod_json = parse_m3u_text_to_json(vod_m3u)
    series_json = parse_series(series_m3u)

    with open("live.json", "w", encoding="utf-8") as f:
        json.dump(live_json, f, ensure_ascii=False, indent=2)
    with open("vod.json", "w", encoding="utf-8") as f:
        json.dump(vod_json, f, ensure_ascii=False, indent=2)
    with open("series.json", "w", encoding="utf-8") as f:
        json.dump(series_json, f, ensure_ascii=False, indent=2)

    print("Bitti. 3 dosya oluştu: live.json, vod.json, series.json")

if __name__ == "__main__":
    main()
