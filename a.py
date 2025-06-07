import asyncio
from playwright.async_api import async_playwright

async def print_episode_html(episode_number):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # True yaparsan arka planda çalışır
        page = await browser.new_page()
        await page.goto("https://animeheaven.me/anime.php?h0xu8")
        await page.wait_for_selector("a[href='gate.php']")

        links = await page.query_selector_all("a[href='gate.php']")
        found = False
        for link in links:
            num_div = await link.query_selector(".watch2")
            if num_div:
                text = (await num_div.inner_text()).strip()
                if text == str(episode_number):
                    await link.click()
                    found = True
                    break

        if not found:
            print(f"Bölüm {episode_number} bulunamadı.")
            await browser.close()
            return

        # Yeni sekmeye geç
        if len(page.context.pages) > 1:
            new_page = page.context.pages[-1]
        else:
            new_page = page

        await new_page.wait_for_load_state('load')
        html_content = await new_page.content()
        print(f"\n--- Bölüm {episode_number} gate.php HTML kaynağı ---\n")
        print(html_content)
        await browser.close()

# 9. bölüm için çağır:
asyncio.run(print_episode_html(9))
