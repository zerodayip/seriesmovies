from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Mediafire linkini buraya gir
mediafire_url = "https://www.mediafire.com/file/8lyizr4y1l5v91u/zuihou-de-zhaohuan-shi-11-bolum.mp4/file"

# (Eğer sadece konsolda görünmesini istersen indir klasörü ayarlamana gerek yok)
options = Options()
options.add_argument("--headless")  # Tarayıcıyı görünmez açmak için (istemiyorsan kaldırabilirsin)
driver = webdriver.Chrome(options=options)

driver.get(mediafire_url)
time.sleep(5)  # Sayfa tamamen yüklensin diye biraz bekle

try:
    # Download butonunu bul
    download_button = driver.find_element(By.CSS_SELECTOR, 'a#downloadButton')
    real_link = download_button.get_attribute("href")
    print("Gerçek indirme linki:", real_link)
except Exception as e:
    print("Download linki bulunamadı!", e)

driver.quit()
