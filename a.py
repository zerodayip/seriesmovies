import sys
from playwright.sync_api import sync_playwright

def print_full_html(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            viewport={"width": 375, "height": 812},
            java_script_enabled=True,
        )
        page = context.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)  # sayfanın tam yüklenmesini beklemek için 3 saniye
        html = page.content()
        print(html)
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_playwright.py <mediafire-link>")
        sys.exit(1)
    print_full_html(sys.argv[1])
