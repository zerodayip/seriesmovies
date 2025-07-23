import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://anizm.com.tr/tavsiyeRobotu")

        # İstediğin yılları seç (örneğin 2025 ve 2024)
        await page.select_option("#years", ["2025", "2024"])

        # Sonuçların yüklenmesi için bekle (isteğe bağlı, network idle veya timeout)
        await page.wait_for_timeout(3000)

        # Anime başlıkları ve linklerini seç
        results = await page.query_selector_all("div.aramaSonucItem a.titleLink")

        for r in results:
            href = await r.get_attribute("href")
            title = (await r.inner_text()).strip()
            full_link = href if href.startswith("http") else "https://anizm.com.tr" + href
            print(f"{title}: {full_link}")

        await browser.close()

asyncio.run(main())

