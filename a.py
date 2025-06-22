from playwright.sync_api import sync_playwright
import time

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
        print(f"Film: {title_text} | Rating: {rating_text} | Yıl: {anayil_text}")

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
