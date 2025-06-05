import sys
import requests
from playwright.sync_api import sync_playwright, TimeoutError

def get_download_button_href(url):
    # Mobil cihaz profiliyle sayfayı açıp downloadButton'un href'ini alır
    with sync_playwright() as p:
        iphone = p.devices["Galaxy S20 Ultra"]
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**iphone)
        page = context.new_page()
        page.goto(url, timeout=60000)
        try:
            # Download butonu DOM'a eklenene kadar bekle
            page.wait_for_selector("a#downloadButton", timeout=20000)
            href = page.get_attribute("a#downloadButton", "href")
            if href:
                # Bazı durumlarda href "//www.mediafire.com/..." ile başlar
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = "https://www.mediafire.com" + href
                return href
            else:
                print("Download button var ama href yok!")
                return None
        except TimeoutError:
            print("Download button DOM'a hiç gelmedi!")
            return None
        finally:
            browser.close()

def get_final_download_url(redirect_url):
    # GET isteğiyle gerçek download URL'sini yakalar
    try:
        # Stream açık, allow_redirects=True ile son linki bul
        resp = requests.get(redirect_url, allow_redirects=True, stream=True, timeout=30)
        print("Son (final) indirme linki:", resp.url)
        return resp.url
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_download_final.py <mediafire-link>")
        sys.exit(1)
    
    mediafire_page_url = sys.argv[1]

    print("Mediafire dosya sayfası:", mediafire_page_url)
    print("Buton href'i çekiliyor...")

    download_href = get_download_button_href(mediafire_page_url)

    if download_href:
        print("Download button href:", download_href)
        print("Gerçek indirme linki takip ediliyor...")
        get_final_download_url(download_href)
    else:
        print("Hiçbir indirme linki bulunamadı.")
