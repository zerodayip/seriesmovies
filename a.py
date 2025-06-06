import asyncio
from playwright.async_api import async_playwright
import requests
import re

async def get_embed_links(video_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(video_url)
        await page.wait_for_selector('.parilda', timeout=10000)  # max 10sn bekle

        # .parilda elementlerini çek
        parilda_elements = await page.query_selector_all('.parilda')
        embed_ids = []
        for element in parilda_elements:
            data_embed = await element.get_attribute('data-embed')
            if data_embed:
                embed_ids.append(data_embed)
        await browser.close()

        embed_links = []
        for embed_id in embed_ids:
            post_url = "https://www.animeizlesene.com/ajax/embed"
            post_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://www.animeizlesene.com",
                "Referer": video_url,
            }
            post_data = {"id": embed_id}

            resp = requests.post(post_url, headers=post_headers, data=post_data, verify=False)
            matches = re.findall(r'src="([^"]+)"', resp.text)
            for url in matches:
                if url.startswith("//"):
                    url = "https:" + url
                embed_links.append(url)
        return embed_links

if __name__ == "__main__":
    import sys
    url = "https://www.animeizlesene.com/serie/kusuriya-no-hitorigoto-484-2-season-21-episode"
    links = asyncio.run(get_embed_links(url))
    print("Bulunan embed linkleri:")
    for i, link in enumerate(links, 1):
        print(f"{i}. {link}")
