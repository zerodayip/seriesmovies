import requests
from bs4 import BeautifulSoup
import re
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

BASE_URL = "https://anizm.com.tr"
PROXY_BASE = "https://zeroipday-zeroipday.hf.space/proxy"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "X-Requested-With": "XMLHttpRequest"
}

session = requests.Session()
session.headers.update(HEADERS)


def retry_request(func, *args, retries=3, delay=1, **kwargs):
    for i in range(retries):
        try:
            response = func(*args, timeout=15, **kwargs)
            time.sleep(delay)
            return response
        except Exception as e:
            print(f"❗ Deneme {i+1} hata: {e}", flush=True)
            if i == retries - 1:
                print("⚠️ Tüm denemeler başarısız.", flush=True)
                return None
            time.sleep(delay)


def safe_name(name):
    name = name.replace(" ", "_")
    return re.sub(r'[^A-Za-z0-9_-]', '', name)


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_episodes(anime_link):
    res = retry_request(session.get, anime_link)
    if res is None:
        return []
    soup = BeautifulSoup(res.content, "html.parser")
    episode_divs = soup.select("div#episodesContent div.three.wide.column a.anizm_colorDefault")
    episodes = []
    for a in episode_divs:
        href = a.get("href")
        title = a.select_one("div.title")
        if href and title:
            full_url = href if href.startswith("http") else BASE_URL + href
            episodes.append({
                "url": full_url,
                "title": title.text.strip()
            })
    return episodes


def extract_video_links(ep_url):
    res = retry_request(session.get, ep_url)
    if res is None:
        return []
    soup = BeautifulSoup(res.content, "html.parser")
    video_buttons = soup.select("a.videoPlayerButtons")
    links = []
    for btn in video_buttons:
        video_url = btn.get("video")
        span = btn.select_one("span")
        label = span.text.strip() if span else "Unknown"
        if video_url:
            links.append({"label": label, "url": video_url})
    return links


def write_season_m3u(anime_name, season_number, episodes, group_title):
    folder = f"anizm/{safe_name(anime_name)}"
    os.makedirs(folder, exist_ok=True)
    filename = f"{folder}/{safe_name(anime_name)}_Sezon_{season_number}.m3u"
    m3u_lines = ["#EXTM3U"]
    for ep in episodes:
        ep_title = ep['title'].upper()
        for v in ep.get("videos", []):
            tvg_name = f"{anime_name.upper()} S{season_number:02d}"
            key = f"{anime_name.upper()} SEZON {season_number} - {ep_title}"
            line = f'#EXTINF:-1 tvg-name="{tvg_name}" group-title="{group_title}",{key} [{v["label"].upper()}]'
            proxy_url = f"{PROXY_BASE}/video?url={v['url']}"
            m3u_lines.append(line)
            m3u_lines.append(proxy_url)

    if len(m3u_lines) == 1:
        print(f"⚠️ {filename} için video linki yok, dosya oluşturulmadı.")
        return False

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    print(f"{filename} dosyasına {len(episodes)} bölüm yazıldı.")
    return True


def main():
    json_path = "anizm/animeler.json"
    animeler = load_json(json_path)
    updated = False

    for anime_link, info in animeler.items():
        anime_name = info.get("group", "Bilinmeyen")
        print(f"\n⏳ {anime_name} işleniyor...")

        episodes = get_episodes(anime_link)
        if not episodes:
            print("⚠️ Bölüm bulunamadı, atlanıyor.")
            continue

        # Her bölüm için video linklerini çek
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(extract_video_links, ep['url']): ep for ep in episodes}
            for future in as_completed(futures):
                ep = futures[future]
                try:
                    videos = future.result()
                    ep['videos'] = videos
                except Exception as e:
                    print(f"❗ Bölüm video linki alınamadı: {e}")
                    ep['videos'] = []

        # İstersen sezonu 1 sabit alıyoruz, ya da animede sezon bilgisi varsa oradan çek
        season_number = 1
        group_title = info.get("group", "ANIMELER")

        success = write_season_m3u(anime_name, season_number, episodes, group_title)
        if success:
            # Yeni anime ise JSON’a ekle, eskileri güncelleme (isteğe bağlı)
            if anime_link not in animeler:
                animeler[anime_link] = info
                updated = True

    if updated:
        save_json(animeler, json_path)
        print(f"\nJSON dosyası güncellendi: {json_path}")
    else:
        print("\nJSON dosyasında güncelleme gerekmedi.")


if __name__ == "__main__":
    main()
