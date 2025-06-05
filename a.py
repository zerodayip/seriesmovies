import sys
from playwright.sync_api import sync_playwright, TimeoutError

def print_download_button_href(url):
    with sync_playwright() as p:
        iphone = p.devices["iPhone 13 Pro"]
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**iphone)
        page = context.new_page()
        page.goto(url, timeout=60000)
        try:
            # 20 saniyeye kadar downloadButton'u bekle
            page.wait_for_selector("a#downloadButton", timeout=20000)
            href = page.get_attribute("a#downloadButton", "href")
            if href and href.startswith("https://download") and "mediafire.com" in href:
                print(href)
            else:
                print("Download link bulunamadı (element geldi ama href yok)!")
        except TimeoutError:
            print("Download button hiç gelmedi, Cloudflare veya başka bir engel olabilir!")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_playwright.py <mediafire-link>")
        sys.exit(1)
    print_download_button_href(sys.argv[1])
