import requests

url = "https://filmkovasi.pw/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()  # Hata varsa Exception fırlatır

    html_content = response.text
    print(html_content)

except requests.exceptions.RequestException as e:
    print(f"Hata oluştu: {e}")
