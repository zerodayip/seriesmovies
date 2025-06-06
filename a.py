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

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("download", on_download)

        print(f"\n--- {mediafire_url} açılıyor ---\n")
        page.goto(mediafire_url, timeout=60000)

        try:
            page.wait_for_selector("a#downloadButton", timeout=20000)
            btn = page.query_selector("a#downloadButton")
            if btn:
                print("\n--- Download butonuna tıklanıyor ---\n")
                btn.click()
                # Diğer sayfalara da event bağla (açılırsa)
                for p2 in context.pages:
                    if p2 != page:
                        p2.on("request", on_request)
                        p2.on("response", on_response)
                        p2.on("download", on_download)
                print("\n--- Download işlemleri için bekleniyor... ---\n")
                page.wait_for_timeout(15000)
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
