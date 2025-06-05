import sys
from playwright.sync_api import sync_playwright, devices

def print_download_button_href(url):
    iphone = devices["iPhone 13 Pro"]  # Playwright’ın hazır cihaz profili
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**iphone)
        page = context.new_page()
        page.goto(url, timeout=60000)
        # 4 saniye bekle, bazen Cloudflare biraz daha geç açılıyor
        page.wait_for_timeout(4000)

        # downloadButton id'li <a>'nın href'ini çek
        href = page.get_attribute("a#downloadButton", "href")
        if href and href.startswith("https://download") and "mediafire.com" in href:
            print(href)
        else:
            print("Download link bulunamadı.")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_playwright.py <mediafire-link>")
        sys.exit(1)
    print_download_button_href(sys.argv[1])
