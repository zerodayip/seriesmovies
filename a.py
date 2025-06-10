import requests

# Hedef video sayfası
url = "https://hdplayersystem.live/video/bd652bf1e9b66171ef77f1e0db2e9c1e"

# Gerçekçi tarayıcı isteği gibi görünmek için header'lar
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.wfilmizle.art/",
    "X-Requested-With": "XMLHttpRequest",
}

try:
    # İsteği gönder
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Tüm HTML içeriğini yazdır
    html = response.text
    print("✅ HTML İÇERİK BAŞLANGICI\n")
    print(html)
    print("\n✅ HTML İÇERİK BİTTİ")

except requests.exceptions.RequestException as e:
    print("❌ Hata oluştu:")
    print(e)
