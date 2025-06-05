from playwright.sync_api import sync_playwright
import sys

def get_download_button_href_and_real_link(mediafire_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36")
        page = context.new_page()
        found_download_url = None
        found_dkey_link = None

        def handle_response(response):
            nonlocal found_download_url
            url = response.url
            # mp4, mkv, zip, rar gibi dosya linklerini burada arayabilirsin
            if url.startswith("https://download") and "mediafire.com" in url and (".mp4" in url or ".mkv" in url or ".zip" in url or ".rar" in url):
                found_download_url = url

        page.on("response", handle_response)
        page.goto(mediafire_url, timeout=60000)
        page.wait_for_selector("a#downloadButton", timeout=20000)

        # Dkey içeren download butonunun href'ini çek
        btn = page.query_selector("a#downloadButton")
        if btn:
            found_dkey_link = btn.get_attribute("href")
            print("dkey'li link:", found_dkey_link)
            # Dkey link tam adres değilse tamamlansın
            if found_dkey_link.startswith("//"):
                found_dkey_link = "https:" + found_dkey_link
            elif found_dkey_link.startswith("/"):
                found_dkey_link = "https://www.mediafire.com" + found_dkey_link
            # Butona tıkla
            btn.click()
            page.wait_for_timeout(8000)
        else:
            print("Download butonu bulunamadı!")
            browser.close()
            return

        if found_download_url:
            print("Gerçek download link:", found_download_url)
        else:
            print("Gerçek download link bulunamadı!")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_all_playwright.py <mediafire-page-link>")
        sys.exit(1)
    get_download_button_href_and_real_link(sys.argv[1])
