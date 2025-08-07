# simple_requests.py
import requests

url = "https://yabancidizi.tv/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://google.com/"
}

resp = requests.get(url, headers=headers, timeout=20)
print("Status:", resp.status_code)
print(resp.text)   # tüm HTML terminale basılır

