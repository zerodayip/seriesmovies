import requests

url = "https://dizipalx46.com/"

# User-Agent eklemek genellikle iyi olur, bazı siteler bunu isteyebilir
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers, timeout=15)

# HTML içeriğini yazdır
print(response.text)
