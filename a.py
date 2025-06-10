import requests

url = "https://hdplayersystem.live/video/bd652bf1e9b66171ef77f1e0db2e9c1e"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.wfilmizle.art/",  # Ana site burası
    "X-Requested-With": "XMLHttpRequest",     # AJAX isteği gibi görünmesi için
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # hata varsa Exception fırlatır

    html = response.text
    print("✅ HTML içeriği başarıyla alındı:\n")
    print(html[:2000])  # İlk 2000 karakteri yazdır

except requests.exceptions.RequestException as e:
    print("❌ Hata oluştu:")
    print(e)
