from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.setfilmizle.nl/film/")
    page.wait_for_selector("article.item.dortlu.movies")
    print("1. sayfa yüklendi.")

    # İlk sayfa film linklerini yazdır
    articles1 = page.query_selector_all("article.item.dortlu.movies .poster a")
    for art in articles1:
        print("1. sayfa film:", art.get_attribute("href"))

    # 2. sayfa <span>'ına tıkla!
    page.click("span.page-number[data-page='2']")
    print("2. sayfa butonuna tıklandı.")
    page.wait_for_selector("article.item.dortlu.movies")

    # 2. sayfa film linklerini yazdır
    articles2 = page.query_selector_all("article.item.dortlu.movies .poster a")
    for art in articles2:
        print("2. sayfa film:", art.get_attribute("href"))

    browser.close()
