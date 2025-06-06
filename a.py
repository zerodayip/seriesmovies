from playwright.sync_api import sync_playwright
import sys
import os

def sniff_download_links(mediafire_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        )
        page = context.new_page()

        def on_request(request):
            url = request.url
            if "download" in url:
                print("→ [REQUEST]", request.method, url)

        def on_response(response):
            url = response.url
            if "download" in url:
                print("← [RESPONSE]", response.status, url)

        def on_download(download):
            url = download.url
            print("\n↓↓ [DOWNLOAD EVENT DETECTED]")
            print("  URL:", url)
            print("  Dosya adı:", download.suggested_filename)
            _, ext = os.path.splitext(download.suggested_filename or "")
            print("  Uzantı:", ext)

        # Dinleyicileri ekle
        page.on("request", on_request)
        page.on("response", on_response)
        page.on("download", on_download)

        print(f"\n--- {mediafire_url} açılıyor ---\n")
        page.goto(mediafire_url, timeout=60000)

        # Download butonunu bul ve tıkla, ayrıca dkey linkine de git
        try:
            page.wait_for_selector("a#downloadButton", timeout=20000)
            btn = page.query_selector("a#downloadButton")
            if btn:
                found_dkey_link = btn.get_attribute("href")
                print("\n--- Download butonuna tıklanıyor ---\n")
                btn.click()

                # Eğer dkey linki varsa, yeni bir sayfada aç ve aynı dinleyicileri ekle
                if found_dkey_link:
                    if found_dkey_link.startswith("//"):
                        found_dkey_link = "https:" + found_dkey_link
                    elif found_dkey_link.startswith("/"):
                        found_dkey_link = "https://www.mediafire.com" + found_dkey_link

                    print("\n--- dkey linkine ayrıca gidiliyor: ---")
                    print(found_dkey_link)
                    page2 = context.new_page()
                    page2.on("request", on_request)
                    page2.on("response", on_response)
                    page2.on("download", on_download)
                    page2.goto(found_dkey_link, timeout=60000)
                    page2.wait_for_timeout(10000)  # 10 saniye bekle

                print("\n--- Download işlemleri için bekleniyor... ---\n")
                page.wait_for_timeout(10000)  # 10 saniye bekle
            else:
                print("Download butonu bulunamadı!")
        except Exception as e:
            print("Buton ararken hata:", e)

        print("\n--- İşlem tamamlandı ---\n")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_sniffer_downloadonly.py <mediafire-link>")
        sys.exit(1)
    sniff_download_links(sys.argv[1])
