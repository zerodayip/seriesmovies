import asyncio
from playwright.async_api import async_playwright
import httpx
import re

BASE_URL = "https://anizm.com.tr"

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
    videos = []
    for el in elements:
        video_url = await el.get_attribute("video")
        span = await el.query_selector("span")
        span_text = (await span.inner_text()).strip() if span else ""
        if video_url and ("aincrad" in span_text.lower() or "vidmoly" in span_text.lower()):
            videos.append({"name": span_text, "url": video_url})
    return videos

async def main():
    async with async_playwright() as p, httpx.AsyncClient() as client:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Ana anime sayfası
        main_url = f"{BASE_URL}/tsuyokute-new-saga"
        await page.goto(main_url)
        await page.wait_for_timeout(3000)

        # Anime adı
        title_el = await page.query_selector("h2.anizm_pageTitle a")
        anime_name = (await title_el.inner_text()).strip() if title_el else "Bilinmiyor"

        # Kapak resmi
        meta_img = await page.query_selector("meta[property='og:image']")
        img_content = await meta_img.get_attribute("content") if meta_img else ""
        if img_content and not img_content.startswith("http"):
            img_url = BASE_URL + img_content
        else:
            img_url = img_content

        print(f"Anime Adı: {anime_name}")
        print(f"Kapak Resmi: {img_url}")
        print("\nBölümler ve videolar:")

        # Bölüm linklerini al
        episode_links = await page.query_selector_all("div.episodeBlockList a[href]")
        episode_urls = []
        for a in episode_links:
            href = await a.get_attribute("href")
            if href and href.startswith(BASE_URL):
                episode_urls.append(href)
            elif href:
                episode_urls.append(BASE_URL + href)

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

                # Player ID al
                match = re.search(r'/video/(\d+)', v['url'])
                if match:
                    video_id = match.group(1)
                    player_url = f"{BASE_URL}/player/{video_id}"
                    redirect_url = await fetch_redirect_url(client, player_url)
                    print(f"  Yönlendirme URL: {redirect_url}")
                else:
                    print("  Video ID bulunamadı!")

        await browser.close()

asyncio.run(main())
