import asyncio
from playwright.async_api import async_playwright

async def main():
    url = "https://dizigom1.live/rick-and-morty-1-sezon-1-bolum-hd1/"
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        # Gerekirse biraz bekle ki içerik yüklensin
        await page.wait_for_timeout(3000)
        # div.dizialani içeriğini al
        try:
            dizialani_html = await page.locator("div.dizialani").inner_html()
            print(dizialani_html)
        except Exception as e:
            print("div.dizialani bulunamadı:", e)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
