import requests

# Hedef video sayfası
url = "https://d2.premiumvideo.click/uploads/encode/2dn66q6d3mosqg8gr4xr/1080p/playlist.m3u8"

# Gerçek bir tarayıcı gibi davranan header'lar
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://dizifun3.com",  # Ana sayfa genellikle referer olarak kullanılır
    "X-Requested-With": "XMLHttpRequest"   # AJAX isteği gibi görünmesini sağlar (bazı sunucular bunu ister)
}

try:
    # İsteği gönder
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # HTTP hatası varsa fırlatır

    # Tüm HTML'yi yazdır
    print("✅ HTML İÇERİĞİ BAŞLANGICI\n")
    print(response.text)
    print("\n✅ HTML İÇERİĞİ BİTTİ")

except requests.exceptions.RequestException as e:
    print("❌ Hata oluştu:")
    print(e)
