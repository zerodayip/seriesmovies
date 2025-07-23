import asyncio
from playwright.async_api import async_playwright
import json
import os
import re

BASE_URL = "https://anizm.com.tr"
PROXY_BASE = "https://zeroipday-zeroipday.hf.space/proxy"
JSON_PATH = "anizm/animeler.json"

def safe_name(name):
    name = name.replace(" ", "_")
    return re.sub(r'[^A-Za-z0-9_-]', '', name)

async def get_episodes(page, anime_url):
    await page.goto(anime_url)
    await page.wait_for_timeout(3000)

    episode_links = await page.query_selector_all("div.episodeBlockList a[href]")
    episodes = []
    for a in episode_links:
        href = await a.get_attribute("href")
        title = await a.inner_text()
        if href and title:
            full_url = href if href.startswith("http") else BASE_URL + href
            episodes.append({"url": full_url, "title": title.strip()})
    return episodes

async def get_episode_video_links(page, episode_url):
    await page.goto(episode_url)
    await page.wait_for_timeout(3000)
    elements = await page.query_selector_all("a.videoPlayerButtons")
    videos = []
    for el in elements:
        video_url = await el.get_attribute("video")
        span = await el.query_selector("span")
        span_text = (await span.inner_text()).strip() if span else ""
        if video_url:
            videos.append({"label": span_text, "url": video_url})
    return videos

def write_m3u(anime_name, season_number, episodes, group_title):
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

async def main():
    if not os.path.exists(JSON_PATH):
        print(f"{JSON_PATH} bulunamadı! Lütfen anizm/animeler.json dosyasını oluşturun.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        animeler = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for anime_url, info in animeler.items():
            anime_name = info.get("group") or "Bilinmeyen"
            season_number = info.get("last_season", 1)
            print(f"\n=== İşleniyor: {anime_name} ===")
            print(f"Link: {anime_url}")

            episodes = await get_episodes(page, anime_url)
            print(f"Bölüm sayısı: {len(episodes)}")

            for ep in episodes:
                ep['videos'] = await get_episode_video_links(page, ep['url'])
                print(f"Bölüm: {ep['title']} - Video sayısı: {len(ep['videos'])}")

            yazildi = write_m3u(anime_name, season_number, episodes, group_title="ANİMELER")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
