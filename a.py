import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Sayfa yükleniyor...")
        await page.goto("https://puffytr.com/mattaku-saikin-no-tantei-to-kitara-4-bolum", timeout=60000)

        # JS tarafından oluşturulmasını bekle
        await page.wait_for_selector("iframe", timeout=30000)

        # iframe src'sini al
        iframe_element = await page.query_selector("iframe")
        iframe_src = await iframe_element.get_attribute("src")
        print(f"[+] Iframe: {iframe_src}")

        # iframe'e geç
        iframe_page = await browser.new_page()
        await iframe_page.goto(iframe_src, timeout=60000)

        # data parametresini içeren script tag'ini bul
        await iframe_page.wait_for_selector("script", timeout=30000)

        # Tüm script tag'leri içinde "data=" geçen satırı ara
        scripts = await iframe_page.query_selector_all("script")
        for s in scripts:
            content = await s.inner_text()
            if "data=" in content:
                lines = content.splitlines()
                for line in lines:
                    if "data=" in line:
                        print("[+] BULUNDU SATIR:", line.strip())
                        # data değerini çek
                        import re
                        match = re.search(r'data=["\']([a-f0-9]{32})["\']', line)
                        if match:
                            data_value = match.group(1)
                            print(f"[✅] DATA DEĞERİ: {data_value}")
                            return

        print("[❌] Data değeri bulunamadı.")
        await browser.close()

asyncio.run(main())
