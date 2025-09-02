from playwright.sync_api import sync_playwright

url = "https://yabancidizi.io/"

with sync_playwright() as p:
    # Chromium tarayıcısını başlat (headless modda)
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Sayfayı aç
    page.goto(url)
    
    # Sayfanın tüm HTML içeriğini al
    html = page.content()
    
    print(html)
    
    browser.close()
