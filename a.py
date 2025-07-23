import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://puffytr.com/mattaku-saikin-no-tantei-to-kitara-4-bolum")
        await page.wait_for_timeout(5000)  # 5 saniye bekle DOM tam yüklensin

        # Tüm script'lerde videoID ara
        video_id = await page.evaluate("""
            () => {
                const scripts = Array.from(document.scripts);
                for (const script of scripts) {
                    if (script.textContent.includes("videoID")) {
                        const match = script.textContent.match(/videoID\\s*=\\s*"([^"]+)"/);
                        if (match) return match[1];
                    }
                }
                return null;
            }
        """)

        print("videoID (data):", video_id)

        await browser.close()

asyncio.run(main())
