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
    """Playwright ile sayfayı açıp tüm HTML'yi terminale print eder"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(page_url, timeout=60000)
        page.wait_for_load_state("networkidle")  # tüm network istekleri bitene kadar bekle
        html_content = page.content()
        print(html_content)  # bütün HTML'yi terminale bas
        browser.close()

# --- Kullanım ---
domain = get_current_domain()
if domain:
    page_url = f"{domain}/filmler/"
    print_full_page_html(page_url)
else:
    print("[!] Domain alınamadı.")
