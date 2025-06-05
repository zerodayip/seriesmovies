import sys
from playwright.sync_api import sync_playwright

def follow_download_redirect(url):
    with sync_playwright() as p:
        iphone = p.devices["iPhone 13 Pro"]
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**iphone)
        page = context.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_selector("a#downloadButton", timeout=20000)

        with context.expect_page() as new_page_info:
            page.click("a#downloadButton")
        new_page = new_page_info.value
        new_page.wait_for_load_state("load", timeout=20000)
        # Şimdi yeni açılan sekmede gerçek download linki var mı bakalım
        download_url = new_page.url
        print("Yeni sayfanın adresi:", download_url)

        # Alternatif: yeni sayfadaki download ile başlayan bir link ara
        content = new_page.content()
        import re
        match = re.search(r'https://download[^"\']+mediafire\.com[^"\']+', content)
        if match:
            print("Gerçek download linki:", match.group(0))
        else:
            print("Gerçek download linki bulunamadı.")

        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_playwright.py <mediafire-link>")
        sys.exit(1)
    follow_download_redirect(sys.argv[1])
