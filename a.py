from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.setfilmizle.nl/film/")
    page.wait_for_selector("article.item.dortlu.movies")
    print("1. sayfa yüklendi.")

    # İlk sayfanın ilk film linkini kaydet
    articles1 = page.query_selector_all("article.item.dortlu.movies .poster a")
    film_links_1 = [art.get_attribute("href") for art in articles1]
    print("1. sayfa film sayısı:", len(film_links_1))

    # 2. sayfa <span>'ına tıkla!
    page.click("span.page-number[data-page='2']")
    print("2. sayfa butonuna tıklandı.")

    # Yeni filmler gelene kadar bekle (ilk filmin href'i değişene kadar)
    def first_film_changed():
        els = page.query_selector_all("article.item.dortlu.movies .poster a")
        if not els:
            return False
        return els[0].get_attribute("href") != film_links_1[0]

    # 10 saniye boyunca her 0.5 sn'de kontrol et
    for _ in range(20):
        if first_film_changed():
            break
        time.sleep(0.5)

    articles2 = page.query_selector_all("article.item.dortlu.movies .poster a")
    film_links_2 = [art.get_attribute("href") for art in articles2]
    print("2. sayfa film sayısı:", len(film_links_2))
    for url in film_links_2:
        print("2. sayfa film:", url)

    browser.close()
