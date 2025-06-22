from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

PROXY_PREFIX = "https://zeroipday-zeroipday.hf.space/proxy/vctplay?url="

def get_fastplay_embeds_bs(film_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": film_url,
    }
    embeds = []
    try:
        resp = requests.get(film_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        playex_div = soup.select_one("div#playex")
        nonce = playex_div.get("data-nonce") if playex_div else None
        if not nonce:
            return []
        for btn in soup.select('nav.player a, .idTabs.sourceslist a'):
            if btn.get("data-player-name", "").lower() == "fastplay":
                post_id = btn.get("data-post-id")
                part_key = btn.get("data-part-key", "")
                b_tag = btn.find("b")
                label_main = b_tag.get_text(strip=True) if b_tag else (btn.get_text(strip=True) or "FastPlay")
                if part_key and "dublaj" in part_key.lower():
                    label = "Türkçe Dublaj"
                elif part_key and "altyazi" in part_key.lower():
                    label = "Türkçe Altyazılı"
                elif not part_key:   # part_key yok veya boş ise
                    label = "Türkçe Altyazılı"
                else:
                    label = label_main
                payload = {
                    "action": "get_video_url",
                    "nonce": nonce,
                    "post_id": post_id,
                    "player_name": "FastPlay",
                    "part_key": part_key
                }
                ajax_headers = {
                    "User-Agent": "Mozilla/5.0",
                    "Referer": film_url,
                    "X-Requested-With": "XMLHttpRequest"
                }
                r = requests.post("https://www.setfilmizle.nl/wp-admin/admin-ajax.php", data=payload, headers=ajax_headers, timeout=10)
                try:
                    data = r.json()
                    embed_url = data.get("data", {}).get("url")
                    if embed_url:
                        embeds.append((label, embed_url))
                except Exception:
                    pass
        return embeds
    except Exception:
        return []

def fetch_embed_info(film_info):
    title, rating, anayil, film_link, logo_url = film_info
    fastplay_embeds = get_fastplay_embeds_bs(film_link)
    return (title, rating, anayil, film_link, logo_url, fastplay_embeds)

def gather_film_infos(page):
    articles = page.query_selector_all("article.item.dortlu.movies")
    film_infos = []
    for art in articles:
        title = art.query_selector("h2")
        title_text = title.inner_text().strip() if title else "?"
        rating = art.query_selector("div.imdb span.rating")
        rating_text = rating.inner_text().strip() if rating else "?"
        anayil = art.query_selector("span.anayil")
        anayil_text = anayil.inner_text().strip() if anayil else "?"
        film_link = art.query_selector(".poster a").get_attribute("href")
        poster_img = art.query_selector(".poster img")
        logo_url = poster_img.get_attribute("src") if poster_img else ""
        film_infos.append((title_text, rating_text, anayil_text, film_link, logo_url))
    return film_infos

def print_m3u_entry(title, rating, anayil, label, emb_url, logo_url=None, group_title=None):
    group = group_title or (anayil + " FİLMLERİ")
    logo = logo_url or ""
    info_title = f"{title.upper()} ( IMDB: {rating} | {label.upper()} )"
    # Proxy prefix ile embed url'i birleştir
    m3u_url = PROXY_PREFIX + emb_url
    print(f'#EXTINF:-1 group-title="{group}" tvg-logo="{logo}",{info_title}')
    print(m3u_url)
    print()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.setfilmizle.nl/film/")
    page.wait_for_selector("article.item.dortlu.movies")
    print("1. sayfa yüklendi.")

    film_infos_1 = gather_film_infos(page)

    # 2. sayfa <span>'ına tıkla!
    page.click("span.page-number[data-page='2']")
    print("2. sayfa butonuna tıklandı.")

    # Yeni filmler gelene kadar bekle (ilk filmin başlığı değişene kadar)
    first_film_title = page.query_selector("article.item.dortlu.movies h2").inner_text().strip()
    for _ in range(20):
        try:
            new_title = page.query_selector("article.item.dortlu.movies h2").inner_text().strip()
            if new_title != first_film_title:
                break
        except Exception:
            pass
        time.sleep(0.5)

    film_infos_2 = gather_film_infos(page)
    browser.close()

    # Tüm filmleri birleştir:
    all_film_infos = film_infos_1 + film_infos_2
    print("#EXTM3U\n")
    print(f"# Toplam film: {len(all_film_infos)}\n")

    # Embed linklerini paralel alalım!
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_film = {executor.submit(fetch_embed_info, info): info for info in all_film_infos}
        for future in as_completed(future_to_film):
            title, rating, anayil, film_link, logo_url, fastplay_embeds = future.result()
            for label, emb_url in fastplay_embeds:
                print_m3u_entry(title, rating, anayil, label, emb_url, logo_url)
