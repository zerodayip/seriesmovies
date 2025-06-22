from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.setfilmizle.nl/film/")
    page.wait_for_selector("article.item.dortlu.movies")  # Filmler yüklensin

    # İlk sayfa filmlerini topla
    articles = page.query_selector_all("article.item.dortlu.movies .poster a")
    for art in articles:
        print("Film linki:", art.get_attribute("href"))

    # Sonraki sayfa butonuna tıkla (örneğin sayfa 2)
    page.click("a.page-numbers[aria-label='Sonraki Sayfa']")  # Veya doğru selector
    page.wait_for_selector("article.item.dortlu.movies")

    articles2 = page.query_selector_all("article.item.dortlu.movies .poster a")
    for art in articles2:
        print("2. sayfa film linki:", art.get_attribute("href"))

    browser.close()
