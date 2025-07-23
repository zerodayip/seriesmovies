import asyncio
from playwright.async_api import async_playwright
import httpx
import re

async def fetch_redirect_url(client, player_url):
    try:
        # allow_redirects=False ile yönlendirmeyi takip etme
        resp = await client.get(player_url, follow_redirects=False, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://anizm.com.tr/"
        })
        if resp.status_code in [301,302,303,307,308]:
            return resp.headers.get("location")
        else:
            return None
    except Exception as e:
        print(f"Hata: {e}")
        return None

async def main():
    url = "https://anizm.com.tr/tsuyokute-new-saga-4-bolum-izle"

    async with async_playwright() as p, httpx.AsyncClient() as client:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(5000)  # JS yüklenmesi için bekle

        elements = await page.query_selector_all("a.videoPlayerButtons")

        print("Bulunan video linkleri ve yönlendirme linkleri:")

        for el in elements:
            video_url = await el.get_attribute("video")
            span = await el.query_selector("span")
            span_text = (await span.inner_text()).strip() if span else ""

            if video_url and ("aincrad" in span_text.lower() or "vidmoly" in span_text.lower()):
                print(f"İsim: {span_text}")
                print(f"Video link: {video_url}")

                # Video ID çıkar
                match = re.search(r'/video/(\d+)', video_url)
                if match:
                    video_id = match.group(1)
                    player_url = f"https://anizm.com.tr/player/{video_id}"
                    redirect_url = await fetch_redirect_url(client, player_url)
                    print(f"Yönlendirme URL: {redirect_url}")
                else:
                    print("Video ID bulunamadı!")

                print("------")

        await browser.close()

asyncio.run(main())
