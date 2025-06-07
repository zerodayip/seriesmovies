import requests

url = "https://animeheaven.me/anime.php?h0xu8"

# User-Agent eklemek bazı siteler için gereklidir
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

# Status kontrolü (isteğe bağlı)
if response.status_code == 200:
    print(response.text)
else:
    print(f"Hata oluştu: {response.status_code}")
