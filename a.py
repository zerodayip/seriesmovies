from playwright.sync_api import sync_playwright
import time

def get_all_fastplay_embeds(page, film_url):
    try:
        page.goto(film_url)
        page.wait_for_selector("div#playex", timeout=5000)
        nonce = page.query_selector("div#playex").get_attribute("data-nonce")
        # Tüm FastPlay butonlarını al
        embeds = []
        for btn in page.query_selector_all('nav.player a[data-player-name="FastPlay"]'):
            btn_title = btn.inner_text().strip()
            post_id = btn.get_attribute("data-post-id")
            part_key = btn.get_attribute("data-part-key") or ""
            payload = {
                "action": "get_video_url",
                "nonce": nonce,
                "post_id": post_id,
                "player_name": "FastPlay",
                "part_key": part_key
            }
            ajax_response = page.request.post(
                "https://www.setfilmizle.nl/wp-admin/admin-ajax.php",
                data=payload,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Referer": film_url,
                    "X-Requested-With": "XMLHttpRequest"
                }
            )
            data = ajax_response.json()
            embed_url = data.get("data", {}).get("url")
            if embed_url:
                embeds.append({"label": btn_title, "url": embed_url})
        return embeds
    except Exception as e:
        return []

def print_film_infos(page, page_no):
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

        # Her FastPlay alternatifi için embed linkini yazdır
        fastplay_embeds = get_all_fastplay_embeds(page, film_link)
        if fastplay_embeds:
            for emb in fastplay_embeds:
                print(f"  >>> FastPlay ({emb['label']}): {emb['url']}")
        else:
            print("  >>> FastPlay EMBED: Bulunamadı!")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.setfilmizle.nl/film/")
    page.wait_for_selector("article.item.dortlu.movies")
    print("1. sayfa yüklendi.")

    print_film_infos(page, 1)

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

    print_film_infos(page, 2)
    browser.close()
