import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://anizm.com.tr/tavsiyeRobotu")

        # JS ile multiple select değerlerini ayarla ve change eventi tetikle
        await page.evaluate("""
          () => {
            const select = document.querySelector('#years');
            if (!select) return;
            for (const option of select.options) {
              option.selected = option.value === '2025' || option.value === '2024';
            }
            select.dispatchEvent(new Event('change'));
          }
        """)

        # Sonuçların yüklenmesini bekle
        await page.wait_for_timeout(4000)

        results = await page.query_selector_all("div.aramaSonucItem a.titleLink")

        for r in results:
            href = await r.get_attribute("href")
            title = (await r.inner_text()).strip()
            full_link = href if href.startswith("http") else "https://anizm.com.tr" + href
            print(f"{title}: {full_link}")

        await browser.close()

asyncio.run(main())
