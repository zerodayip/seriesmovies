import asyncio
import os
import json
import re
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

BASE_URL = "https://anizm.com.tr"
PROXY_BASE = "https://zeroipday-zeroipday.hf.space/proxy"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
JSON_PATH = "anizm/yenibolumler.json"

def safe_name(name):
    name = name.replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9_-]", "", name)

def load_series():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_series(data):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_year(soup):
    ul = soup.select_one("ul.anizm_verticalList")
    if ul:
        first_li = ul.find("li")
        if first_li:
            year = re.search(r"\d{4}", first_li.text.strip())
            return year.group(0) if year else "unknown"
    return "unknown"

def extract_cover_url(soup):
    img = soup.select_one("img.infoPosterImgItem")
    if img and img.get("src"):
        return img["src"] if img["src"].startswith("http") else BASE_URL + img["src"]

    header = soup.select_one("header .cover.blurred")
    if header and "style" in header.attrs:
        m = re.search(r"url\(['\"]?(.*?)['\"]?\)", header["style"])
        if m:
            url = m.group(1)
            return url if url.startswith("http") else BASE_URL + url

    meta = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
    if meta and meta.get("content"):
        return meta["content"] if meta["content"].startswith("http") else BASE_URL + meta["content"]

    return ""

def get_episodes(series_url):
    res = requests.get(series_url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")
    episodes = []

    # Bölüm linkleri için selector düzeltildi:
    for a in soup.select("div.episodeBlockList div.content a[href]"):
        href = a.get("href")
        if not href:
            continue
        full_url = href if href.startswith("http") else BASE_URL + href

        # Bölüm numarasını regex ile alıyoruz:
        ep_match = re.search(r"-([0-9]+)-bolum$", href)
        if not ep_match:
            ep_match = re.search(r"-([0-9]+)$", href)

        episode_number = int(ep_match.group(1)) if ep_match else None
        if episode_number is not None:
            episodes.append({
                "name": f"1. Sezon {episode_number}. Bölüm",
                "url": full_url,
                "season": 1,
                "episode": episode_number,
            })
    print(f"📺 Bulunan bölüm sayısı: {len(episodes)}")
    return sorted(episodes, key=lambda ep: ep["episode"])

async def extract_embed_with_playwright(ep_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(ep_url)
        await page.wait_for_timeout(4000)
        embed = None

        buttons = await page.query_selector_all("a.videoPlayerButtons")
        for btn in buttons:
            label = await btn.inner_text()
            label = label.lower()
            if "aincrad" in label:
                video = await btn.get_attribute("video")
                if video and "video/" in video:
                    video_id = video.split("/")[-1]
                    embed = f"{BASE_URL}/player/{video_id}"
                    break

        await browser.close()

        if embed:
            return {
                "host": "aincrad",
                "url": embed,
                "label": "Altyazı"
            }
        print(f"❗ Embed bulunamadı: {ep_url}")
        return None

async def get_embed_links_all(episodes):
    sem = asyncio.Semaphore(3)

    async def fetch_one(ep):
        async with sem:
            link = await extract_embed_with_playwright(ep["url"])
            ep = ep.copy()
            ep["embed_links"] = [link] if link else []
            return ep

    tasks = [fetch_one(ep) for ep in episodes]
    return await asyncio.gather(*tasks)

def write_season_m3u(series_name, poster_url, season_number, episodes, group_title, year):
    folder = f"anizm/{safe_name(series_name)}_{year}"
    os.makedirs(folder, exist_ok=True)
    filename = f"{folder}/{safe_name(series_name)}_Sezon_{season_number}.m3u"

    yazilan_bolumler = []
    m3u_lines = ["#EXTM3U"]

    for ep in episodes:
        links = ep.get("embed_links", [])
        if not links:
            continue
        for l in links:
            sxx = f"S{ep['season']:02d}"
            exx = f"E{ep['episode']:02d}"
            tvg_name = f"{series_name.upper()} {sxx}{exx}"
            key = f"{series_name.upper()} {ep['season']}. SEZON {ep['episode']}. BÖLÜM"
            line = f'#EXTINF:-1 tvg-id="" tvg-name="{tvg_name}" tvg-logo="{poster_url}" group-title="{group_title}",{key} ({l["label"].upper()} | {l["host"].upper()})'
            proxy_url = f"{PROXY_BASE}/{l['host']}?url={l['url']}"
            m3u_lines.append(line)
            m3u_lines.append(proxy_url)
        yazilan_bolumler.append(ep)

    if yazilan_bolumler:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        print(f"✅ {filename} dosyasına {len(yazilan_bolumler)} bölüm yazıldı.")
    else:
        print(f"⚠️ {filename} dosyası yazılmadı.")
    return yazilan_bolumler

async def main():
    takip = load_series()
    for name, info in takip.items():
        print(f"\n🔍 İşleniyor: {name}")
        try:
            res = requests.get(name, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")

            year = extract_year(soup)
            title_el = soup.select_one("h2.anizm_pageTitle a")
            title = title_el.text.strip() if title_el else "Bilinmeyen"
            poster_url = extract_cover_url(soup)
            group_title = info.get("group", "YENİ ANİME")

            episodes = get_episodes(name)
            last_season = info.get("last_season", 1)
            last_episode = info.get("last_episode", 0)
            start_episode = info.get("start_episode", 1)

            yeni_bolumler = [ep for ep in episodes if ep["episode"] >= start_episode and ep["episode"] > last_episode]
            if not yeni_bolumler:
                print("✅ Yeni bölüm bulunamadı.")
                continue

            yeni_bolumler = await get_embed_links_all(yeni_bolumler)
            yazilacak_eps = [ep for ep in yeni_bolumler if ep.get("embed_links")]
            if not yazilacak_eps:
                print("⚠️ Embed linki olmayan bölüm.")
                continue

            yazilanlar = write_season_m3u(title, poster_url, 1, yazilacak_eps, group_title, year)
            if yazilanlar:
                son = max(yazilanlar, key=lambda ep: ep["episode"])
                takip[name]["last_season"] = 1
                takip[name]["last_episode"] = son["episode"]

            time.sleep(1)
        except Exception as e:
            print(f"🚫 HATA: {e}")
            continue

    save_series(takip)

if __name__ == "__main__":
    if not os.path.exists("anizm"):
        os.makedirs("anizm")
    asyncio.run(main())
