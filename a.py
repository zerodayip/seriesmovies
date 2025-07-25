import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("https://www.croxyproxy.com/")

        # URL input alanına istediğini yaz
        await page.fill("#url", "https://animeizlesene.com/series")

        # Formu submit et
        await page.click('form#request button[type="submit"]')  # genelde buton olur

        # Yeni sayfanın yüklenmesini bekle
        await page.wait_for_load_state("networkidle")

        # Artık içerik proxy üzerinden geliyor
        print(await page.title())
        content = await page.content()
        print(content[:1000])  # İlk 1000 karakteri yaz

        await browser.close()

asyncio.run(main())

