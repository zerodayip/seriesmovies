import requests
import re
import sys
from playwright.sync_api import sync_playwright

def get_dkey_download_link(mediafire_page_url):
    """Mediafire sayfa linkinden dkey içeren indir linkini çeker."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    }
    resp = requests.get(mediafire_page_url, headers=headers)
    if resp.status_code != 200:
        print("Mediafire sayfası alınamadı:", resp.status_code)
        return None
    # Download butonu id="downloadButton"
    match = re.search(r'<a[^>]*id="downloadButton"[^>]*href="([^"]+)"', resp.text)
    if match:
        href = match.group(1)
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://www.mediafire.com" + href
        return href
    print("Download butonu veya href bulunamadı!")
    return None

def get_real_download_link_from_network(dkey_url):
    """Dkey linkini Playwright ile açıp ağdan gerçek indirme linkini bulur."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36")
        page = context.new_page()
        found = None

        def handle_response(response):
            nonlocal found
            url = response.url
            # .mp4, .mkv, .zip... dosya uzantılarını ekleyebilirsin
            if url.startswith("https://download") and "mediafire.com" in url and (".mp4" in url or ".mkv" in url or ".zip" in url):
                found = url

        page.on("response", handle_response)
        page.goto(dkey_url, timeout=60000)
        page.wait_for_selector("a#downloadButton", timeout=20000)
        page.click("a#downloadButton")
        page.wait_for_timeout(8000)
        browser.close()
        return found

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_auto_extract.py <mediafire-page-link>")
        sys.exit(1)
    page_url = sys.argv[1]
    print("Sayfa:", page_url)
    dkey_link = get_dkey_download_link(page_url)
    if not dkey_link:
        print("dkey içeren link bulunamadı!")
        sys.exit(1)
    print("Dkey/dkey'li link:", dkey_link)
    real_link = get_real_download_link_from_network(dkey_link)
    if real_link:
        print("Gerçek download link:", real_link)
    else:
        print("Gerçek download linki bulunamadı!")
