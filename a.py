import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/",
    # Başka header eklemek de yardımcı olabilir
}

r = requests.get("https://www.mediafire.com/file/8lyizr4y1l5v91u/zuihou-de-zhaohuan-shi-11-bolum.mp4/file", headers=headers)
print(r.text)
