import requests

# Site URL'si
url = "https://gofilmizle.com/"

# Header eklemek, bazı sitelerin botları engellememesi için faydalı olur
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# GET isteği gönder
response = requests.get(url, headers=headers)

# HTTP isteğinin başarılı olup olmadığını kontrol et
if response.status_code == 200:
    html_content = response.text
    print(html_content)  # HTML çıktısını yazdır
else:
    print(f"İstek başarısız oldu. Status code: {response.status_code}")
