from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import sys

MOBILE_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Mobile Safari/537.36"
)
WINDOW_SIZE = "412,915"  # Galaxy S23 Ultra çözünürlüğü

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument(f"--window-size={WINDOW_SIZE}")
chrome_options.add_argument(f"--user-agent={MOBILE_USER_AGENT}")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=chrome_options)

if len(sys.argv) < 2:
    print("Kullanım: python mobile_mediafire.py <mediafire-link>")
    driver.quit()
    sys.exit(1)

mediafire_url = sys.argv[1]
driver.get(mediafire_url)

# Download butonunu bekle (en fazla 20 saniye)
for _ in range(20):
    try:
        btn = driver.find_element(By.ID, "downloadButton")
        break
    except:
        time.sleep(1)
else:
    print("Download button bulunamadı!")
    driver.quit()
    sys.exit(1)

href = btn.get_attribute("href")
print("Mobil tarayıcıda download butonu href:", href)

driver.quit()
