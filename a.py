import requests

url = "https://aniworld.to/anime/stream/from-old-country-bumpkin-to-master-swordsman"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
}

response = requests.get(url, headers=headers)
print(response.text)
