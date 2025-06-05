from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
# JavaScript'i kapat (en güncel yol)
chrome_options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.javascript": 2
})

driver = webdriver.Chrome(options=chrome_options)

# Artık JS devre dışı! İlk istekte bile JS çalışmaz.
driver.get("https://www.mediafire.com/file/8lyizr4y1l5v91u/zuihou-de-zhaohuan-shi-11-bolum.mp4/file")

html = driver.page_source
print(html[:1000])  # örnek: ilk 1000 karakteri yazdır

driver.quit()
