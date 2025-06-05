from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Mediafire linkini buraya gir
mediafire_url = "https://www.mediafire.com/file/8lyizr4y1l5v91u/zuihou-de-zhaohuan-shi-11-bolum.mp4/file"

options = Options()
options.add_argument("--headless")  # Tarayıcıyı görünmez açmak için (istemezsen kaldırabilirsin)
driver = webdriver.Chrome(options=options)

driver.get(mediafire_url)
time.sleep(5)  # Sayfa tamamen yüklensin

# Tüm HTML'yi al ve yazdır
html = driver.page_source
print(html)

driver.quit()
