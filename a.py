from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

url = "https://www.animeizlesene.com/serie/kusuriya-no-hitorigoto-484-2-season-21-episode"

options = Options()
options.add_argument("--headless")  # Tarayıcıyı arkaplanda açar, gerekirse kaldırabilirsin
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(url)
time.sleep(5)  # Sayfanın tam yüklenmesi için 5 sn bekle (gerekirse artırabilirsin)

html = driver.page_source
print(html)

driver.quit()
