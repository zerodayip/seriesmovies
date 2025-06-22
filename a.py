# get_embed.py

from playwright.sync_api import sync_playwright

film_url = "https://www.hdfilmcehennemi.men/film/kutsal-damacana-5-zombi/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(film_url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)  # Gerekirse artır

    # Eğer tıklama gerekirse (ör: #fimcnt_pb butonunu bulup tıkla)
    try:
        page.click("#fimcnt_pb")
        page.wait_for_timeout(1500)
    except Exception:
        pass

    iframe = page.query_selector("iframe")
    if iframe:
        src = iframe.get_attribute("src")
        print(src)
    else:
        print("iframe bulunamadı.")

    browser.close()
