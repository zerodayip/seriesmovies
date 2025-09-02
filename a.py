import requests

url = "https://dizilla.club/"

# HTTP isteği gönder
response = requests.get(url)

# Başarılı bir yanıt alındıysa
if response.status_code == 200:
    # Sayfanın tüm HTML içeriğini yazdır
    print(response.text)
else:
    print("Sayfa alınamadı. HTTP Durum Kodu:", response.status_code)
