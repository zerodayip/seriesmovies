from playwright.sync_api import sync_playwright
import sys
import os

def get_everything(mediafire_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Dilersen True yapabilirsin
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        )
        page = context.new_page()

        # Tüm istekleri dinle (requestler)
        def on_request(request):
            print("→ [REQUEST]", request.method, request.url)

        # Tüm response'ları dinle
        def on_response(response):
            print("← [RESPONSE]", response.status, response.url)

        # Download event'i dinle (gerçek dosya iniyorsa)
        def on_download(download):
            print("↓↓ [DOWNLOAD EVENT]")
            print("  URL:", download.url)
            print("  Dosya adı:", download.suggested_filename)
            _, ext = os.path.splitext(download.suggested_filename or "")
            print("  Uzantı:", ext)
            # Otomatik kaydetme kapalı! İstersen download.save_as ile dosyayı kaydedebilirsin.

        # Tüm page event'lerini bağla
        page.on("request", on_request)
        page.on("response", on_response)
        page.on("download", on_download)

        print(f"\n--- Mediafire sayfasına gidiliyor: {mediafire_url} ---\n")
        page.goto(mediafire_url, timeout=60000)

        # Download butonunu bul, varsa tıkla
        try:
            page.wait_for_selector("a#downloadButton", timeout=20000)
            btn = page.query_selector("a#downloadButton")
            if btn:
                print("\n--- Download butonuna tıklanıyor ---\n")
                btn.click()
                # Bazen yeni sekmede açabiliyor, bütün context için dinleme açıyoruz:
                for p2 in context.pages:
                    if p2 != page:
                        p2.on("request", on_request)
                        p2.on("response", on_response)
                        p2.on("download", on_download)
                # Tüm eventlerin tetiklenmesi için bekle
                print("\n--- Download işlemleri için bekleniyor... ---\n")
                page.wait_for_timeout(15000)  # 15 saniye bekle, gerekirse uzatabilirsin
            else:
                print("Download butonu bulunamadı!")
        except Exception as e:
            print("Buton ararken hata:", e)

        print("\n--- İşlem bitti ---\n")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_full_sniffer.py <mediafire-link>")
        sys.exit(1)
    get_everything(sys.argv[1])
