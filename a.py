import asyncio
from playwright.async_api import async_playwright
import requests
import json

BASE_URL = "https://www.setfilmizle.my"
AJAX_URL = f"{BASE_URL}/wp-admin/admin-ajax.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0 Safari/537.36",
    "Referer": BASE_URL,
    "X-Requested-With": "XMLHttpRequest",
}

# 1. Playwright ile nonce çek
async def get_nonce():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(BASE_URL, timeout=60000)

        nonce_data = await page.evaluate("() => window.STMOVIE_AJAX?.nonces")
        await browser.close()

        if not nonce_data or "pagination" not in nonce_data:
            raise RuntimeError("Pagination nonce bulunamadı!")

        return nonce_data["pagination"]

# 2. Requests ile film verilerini çek
def get_films(pagination_nonce, page=1):
    payload = {
        "action": "stm_pagination_load",
        "nonce": pagination_nonce,
        "page": page,
    }
    resp = requests.post(AJAX_URL, headers=HEADERS, data=payload)
    resp.raise_for_status()
    return resp.json()

# 3. Ana çalışma
async def main():
    nonce = await get_nonce()
    print("[+] Pagination nonce alındı:", nonce)

    # Örnek: İlk 3 sayfa film çek
    for page in range(1, 4):
        data = get_films(nonce, page)
        print(f"\n--- Sayfa {page} ---")
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
