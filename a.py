import requests

url = "https://vctplay.site/video/PBlraADfkJit"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://vctplay.site/",  # veya gerekiyorsa tam sayfa
    # "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7" # İstersen ekleyebilirsin
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print(response.text)  # HTML kaynağını ekrana yazdırır
else:
    print(f"Sayfa çekilemedi! Status kodu: {response.status_code}")

