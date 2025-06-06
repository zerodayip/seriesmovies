from playwright.sync_api import sync_playwright

def get_download_link(mediafire_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 14; SM-S908E) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/28.0 Chrome/112.0.0.0 Mobile Safari/537.36"
        )
        page = context.new_page()
        page.goto(mediafire_url, timeout=60000)
        page.wait_for_timeout(2000)  # Gerekirse artır

        btn = page.query_selector("a#downloadButton")
        if btn:
            href = btn.get_attribute("href")
            print("HTML'deki link:", href)
        else:
            print("Download butonu bulunamadı!")
        browser.close()

if __name__ == "__main__":
    # Örnek kullanım:
    # get_download_link("https://www.mediafire.com/file/...")
    import sys
    if len(sys.argv) < 2:
        print("Kullanım: python samsung_download_link.py <mediafire-link>")
    else:
        get_download_link(sys.argv[1])
