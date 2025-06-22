import requests

url = "https://vctplay.site/manifests/PBlraADfkJit/master.txt"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://vctplay.site/video/PBlraADfkJit"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print(response.text)
else:
    print(f"Dosya alınamadı! Status kodu: {response.status_code}")
