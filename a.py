import sys
from playwright.sync_api import sync_playwright

def print_download_button_href(url):
    with sync_playwright() as p:
        iphone = p.devices["iPhone 13 Pro"]  # Doğru cihaz profili erişimi!
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**iphone)
        page = context.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)  # Cloudflare için bekleme

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
