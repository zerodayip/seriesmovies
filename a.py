import requests

url = "https://yabancidizi.io/"

# Tarayıcı gibi görünmek için header ekleyelim
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/139.0.0.0 Safari/537.36",
    "Referer": "https://yabancidizi.io/",
    "Header" : "https://yabancidizi.io/" # İsteğe bağlı, bazı siteler için gerekli
}

# HTTP isteği gönder
response = requests.get(url, headers=headers)

# Yanıtı kontrol et
if response.status_code == 200:
    print(response.text)  # Sayfanın tüm HTML içeriği
else:
    print("Sayfa alınamadı. HTTP Durum Kodu:", response.status_code)
