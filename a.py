import asyncio
from playwright.async_api import async_playwright
import httpx
import re
import json
import os

BASE_URL = "https://anizm.com.tr"
ANIMES_JSON_PATH = "anizm/animeler.json"  # Json dosya yolu

async def fetch_redirect_url(client, player_url):
    try:
        resp = await client.get(player_url, follow_redirects=False, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": BASE_URL + "/"
        })
        if resp.status_code in [301,302,303,307,308]:
            return resp.headers.get("location")
        else:
            return None
    except Exception as e:
        print(f"Hata: {e}")
        return None

async def get_episode_video_links(page, episode_url):
    await page.goto(episode_url)
    await page.wait_for_timeout(3000)  # JS yüklenmesi için bekle

    elements = await page.query_selector_all("a.videoPlayerButtons")
    aincrad_videos = []
    vidmoly_videos = []
    for el in elements:
        video_url = await el.get_attribute("video")
        span = await el.query_selector("span")
        span_text = (await span.inner_text()).strip() if span else ""

        if video_url:
            text_lower = span_text.lower()
            if "aincrad" in text_lower:
                aincrad_videos.append({"name": span_text, "url": video_url})
            elif "vidmoly" in text_lower:
                vidmoly_videos.append({"name": span_text, "url": video_url})

    if aincrad_videos:
        return aincrad_videos
    elif vidmoly_videos:
        return vidmoly_videos
    else:
        return []

async def extract_cover_url(page):
    # 1. Öncelik: img.infoPosterImgItem
    img_el = await page.query_selector("img.infoPosterImgItem")
    if img_el:
        src = await img_el.get_attribute("src")
        if src:
            return src if src.startswith("http") else BASE_URL + src

    # 2. İkinci öncelik: header > div.cover style içindeki background url(...)
    cover_div = await page.query_selector("header .cover.blurred")
    if cover_div:
        style = await cover_div.get_attribute("style") or ""
        m = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
        if m:
            url = m.group(1)
            return url if url.startswith("http") else BASE_URL + url

    # 3. Son çare meta tag
    meta_img = await page.query_selector("meta[property='og:image']")
    if not meta_img:
        meta_img = await page.query_selector("meta[name='og:image']")
    if meta_img:
        content = await meta_img.get_attribute("content")
        if content:
            return content if content.startswith("http") else BASE_URL + content

    return "Kapak resmi bulunamadı"

async def process_anime(page, client, anime_url, anime_name=None):
    await page.goto(anime_url)
    await page.wait_for_timeout(3000)

    # Anime adı sayfadan al, parametre boşsa
    if not anime_name:
        title_el = await page.query_selector("h2.anizm_pageTitle a")
        anime_name = (await title_el.inner_text()).strip() if title_el else "Bilinmiyor"

    # Kapak resmi
    cover_url = await extract_cover_url(page)

    print(f"\n=== Anime: {anime_name} ===")
    print(f"Kapak Resmi: {cover_url}")

    # Bölüm linklerini al
    episode_links = await page.query_selector_all("div.episodeBlockList a[href]")
    episode_urls = []
    for a in episode_links:
        href = await a.get_attribute("href")
        if href:
            full_url = href if href.startswith("http") else BASE_URL + href
            episode_urls.append(full_url)

    # Her bölüm için video linklerini al, player yönlendirmesini çek ve yazdır
    for ep_url in episode_urls:
        print(f"\nBölüm URL: {ep_url}")
        videos = await get_episode_video_links(page, ep_url)
        if not videos:
            print("  Video bulunamadı.")
            continue

        for v in videos:
            print(f"  Video İsmi: {v['name']}")
            print(f"  Video Linki: {v['url']}")

            match = re.search(r'/video/(\d+)', v['url'])
            if match:
                video_id = match.group(1)
                player_url = f"{BASE_URL}/player/{video_id}"
                redirect_url = await fetch_redirect_url(client, player_url)
                print(f"  Yönlendirme URL: {redirect_url}")
            else:
                print("  Video ID bulunamadı!")

async def main():
    if not os.path.exists(ANIMES_JSON_PATH):
        print(f"Hata: '{ANIMES_JSON_PATH}' dosyası bulunamadı.")
        return

    with open(ANIMES_JSON_PATH, "r", encoding="utf-8") as f:
        anime_data = json.load(f)

    async with async_playwright() as p, httpx.AsyncClient() as client:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for anime_url, info in anime_data.items():
            anime_name = info.get("group")
            await process_anime(page, client, anime_url, anime_name)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
