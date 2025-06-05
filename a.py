import sys
from playwright.sync_api import sync_playwright

def get_mediafire_direct_link(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            viewport={"width": 375, "height": 812},
            java_script_enabled=True,
        )
        page = context.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_selector("#downloadButton", timeout=60000)
        link = page.get_attribute("#downloadButton", "href")
        print(link if link else "Bulunamadı.")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_playwright.py <mediafire-link>")
        sys.exit(1)
    get_mediafire_direct_link(sys.argv[1])
