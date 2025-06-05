from playwright.sync_api import sync_playwright
import sys

def find_real_download_url(mediafire_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36")
        page = context.new_page()
        found = None

        def handle_response(response):
            nonlocal found
            url = response.url
            # Gerçek indirme linkini filtrele
            if url.startswith("https://download") and "mediafire.com" in url and url.endswith(".mp4"):
                found = url

        page.on("response", handle_response)
        page.goto(mediafire_url, timeout=60000)
        page.wait_for_selector("a#downloadButton", timeout=20000)
        page.click("a#downloadButton")
        page.wait_for_timeout(8000)  # İsteklerin gelmesini bekle

        if found:
            print("Gerçek download link:", found)
        else:
            print("Gerçek link bulunamadı!")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_network_extract.py <mediafire-link>")
        sys.exit(1)
    find_real_download_url(sys.argv[1])
