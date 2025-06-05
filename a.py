import sys
from playwright.sync_api import sync_playwright

def save_full_html(url):
    with sync_playwright() as p:
        iphone = p.devices["iPhone 13 Pro"]
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**iphone)
        page = context.new_page()
        page.goto(url, timeout=60000)
        # 20 saniyeye kadar download butonunun gelmesini bekle (opsiyonel)
        try:
            page.wait_for_selector("a#downloadButton", timeout=20000)
        except:
            pass  # Buton gelmese bile HTML'yi alalım

        html = page.content()
        with open("html.txt", "w", encoding="utf-8") as f:
            f.write(html)
        print("Sayfa kaydedildi: html.txt")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_playwright.py <mediafire-link>")
        sys.exit(1)
    save_full_html(sys.argv[1])
