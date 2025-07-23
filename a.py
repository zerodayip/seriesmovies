import asyncio
from playwright.async_api import async_playwright
import re

async def main():
    url = "https://anizm.com.tr/tsuyokute-new-saga-4-bolum-izle"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # headless=True görünmez mod
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(5000)  # 5 saniye bekle, JS yüklenmesi için

        content = await page.content()

        # regex ile video linklerini bul
        video_links = set(re.findall(r'https://anizm\.com\.tr/video/\d+', content))

        print("Bulunan video linkleri:")
        for link in video_links:
            print(link)

        await browser.close()

asyncio.run(main())
