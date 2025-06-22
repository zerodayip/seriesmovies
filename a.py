from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup
import time

def get_fastplay_embeds_bs(film_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": film_url,
    }
    embeds = []
    try:
        resp = requests.get(film_url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        playex_div = soup.select_one("div#playex")
        nonce = playex_div.get("data-nonce") if playex_div else None
        if not nonce:
            return []
        for btn in soup.select("nav.player a"):
            if btn.get("data-player-name", "").lower() == "fastplay":
                post_id = btn.get("data-post-id")
                part_key = btn.get("data-part-key", "")
                label = btn.text.strip() or "FastPlay"
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
                r = requests.post("https://www.setfilmizle.nl/wp-admin/admin-ajax.php", data=payload, headers=ajax_headers, timeout=15)
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

def print_film_infos_with_embed(page, page_no):
    articles = page.query_selector_all("article.item.dortlu.movies")
    print(f"\n{page_no}. sayfa film sayısı: {len(articles)}")
    for art in articles:
        title = art.query_selector("h2")
        title_text = title.inner_text().strip() if title else "?"
        rating = art.query_selector("div.imdb span.rating")
        rating_text = rating.inner_text().strip() if rating else "?"
        anayil = art.query_selector("span.anayil")
        anayil_text = anayil.inner_text().strip() if anayil else "?"
        film_link = art.query_selector(".poster a").get_attribute("href")
        print(f"\nFilm: {title_text} | Rating: {rating_text} | Yıl: {anayil_text} | Link: {film_link}")

        # Her film için embed linkleri:
        fastplay_embeds = get_fastplay_embeds_bs(film_link)
        if fastplay_embeds:
            for label, emb_url in fastplay_embeds:
                print(f"  >>> FastPlay ({label}): {emb_url}")
        else:
            print("  >>> FastPlay EMBED: Bulunamadı!")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.setfilmizle.nl/film/")
    page.wait_for_selector("article.item.dortlu.movies")
    print("1. sayfa yüklendi.")

    print_film_infos_with_embed(page, 1)

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

    print_film_infos_with_embed(page, 2)
    browser.close()
