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

def get_film_links_with_playwright(page_url):
    """Playwright ile sayfayı açıp JS ile yüklenen film linklerini çeker"""
    links = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(page_url, timeout=60000)
        page.wait_for_selector("div#content-holder article.item.dortlu.movies", timeout=15000)

        articles = page.query_selector_all("div#content-holder article.item.dortlu.movies")
        for art in articles:
            a_tag = art.query_selector("div.poster a")
            if a_tag:
                href = a_tag.get_attribute("href")
                if href:
                    links.append(href)
        browser.close()
    return links

# --- Kullanım ---
domain = get_current_domain()
if domain:
    page_url = f"{domain}/filmler/"
    film_links = get_film_links_with_playwright(page_url)
    if film_links:
        print("Film Linkleri:")
        for link in film_links:
            print(link)
    else:
        print("[!] Film linkleri bulunamadı.")
else:
    print("[!] Domain alınamadı.")
