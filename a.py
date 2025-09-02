from playwright.sync_api import sync_playwright
import requests

# Proxy listesi URL'si
proxy_list_url = "https://www.proxyscrape.com/free-proxy-list/turkey"

# Proxy listesini çekme
response = requests.get(proxy_list_url)
proxy_list = response.text.splitlines()

# Proxy'leri sırayla deneme
for proxy in proxy_list:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                proxy={"server": f"http://{proxy}"}
            )
            page = context.new_page()
            page.goto("https://yabancidizi.io/")
            html_content = page.content()
            browser.close()

            # Başarılıysa HTML içeriğini yazdırma
            print("Proxy ile erişim başarılı!")
            print(html_content)
            break
    except Exception as e:
        print(f"Proxy {proxy} ile erişim sağlanamadı: {e}")
