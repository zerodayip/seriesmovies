from playwright.sync_api import sync_playwright
import requests

def get_current_domain():
    """GitHub raw linkinden güncel domaini alır"""
    url = "https://raw.githubusercontent.com/zerodayip/seriesmovies/refs/heads/main/domain/setfimizle.txt"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        for line in r.text.splitlines():
            line = line.strip()
            if line.startswith("http"):
                return line.rstrip("/")  # sondaki / kaldır
    except Exception as e:
        print(f"[!] Domain alınamadı: {e}")
    return None

def print_full_page_html(page_url):
    """Playwright ile sayfayı açıp tüm HTML'yi print eder"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(page_url, timeout=60000)  # Sayfayı aç
        page.wait_for_load_state("networkidle")  # Tüm network isteklerinin bitmesini bekle
        html_content = page.content()  # Sayfanın full HTML içeriği
        print(html_content)
        browser.close()

# --- Kullanım ---
domain = get_current_domain()
if domain:
    page_url = f"{domain}/filmler/"
    print_full_page_html(page_url)
else:
    print("[!] Domain alınamadı.")
