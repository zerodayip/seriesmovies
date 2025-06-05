from playwright.sync_api import sync_playwright
import sys

def get_download_button_href_and_real_link(mediafire_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        )
        page = context.new_page()
        found_download_url = None

        def handle_response(response):
            url = response.url
            print("AĞ:", url)
            if url.startswith("https://download") and "mediafire.com" in url and (
                url.endswith(".mp4")
                or url.endswith(".mkv")
                or url.endswith(".zip")
                or url.endswith(".rar")
            ):
                nonlocal found_download_url
                found_download_url = url

        page.on("response", handle_response)
        page.goto(mediafire_url, timeout=60000)
        page.wait_for_selector("a#downloadButton", timeout=20000)

        # Dkey içeren download butonunun href'ini çek
        btn = page.query_selector("a#downloadButton")
        if not btn:
            print("Download butonu bulunamadı!")
            browser.close()
            return

        found_dkey_link = btn.get_attribute("href")
        print("dkey'li link:", found_dkey_link)
        # Dkey link tam adres değilse tamamla
        if found_dkey_link.startswith("//"):
            found_dkey_link = "https:" + found_dkey_link
        elif found_dkey_link.startswith("/"):
            found_dkey_link = "https://www.mediafire.com" + found_dkey_link

        # Şimdi dkey'li linke tekrar GET at ve ağı dinle!
        page.goto(found_dkey_link, timeout=60000)
        page.wait_for_timeout(15000)  # 15 saniye bekle (gerekirse artır)

        if found_download_url:
            print("\nGerçek download link:", found_download_url)
        else:
            print("Gerçek download link bulunamadı!")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_all_playwright.py <mediafire-page-link>")
        sys.exit(1)
    get_download_button_href_and_real_link(sys.argv[1])
