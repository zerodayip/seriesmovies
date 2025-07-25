import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_until_no_more_links(base_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    page = 1
    anime_data = {}

    while True:
        url = f"{base_url}&page={page}"
        print(f"\n🟢 {page}. Sayfa anime adları:", flush=True)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Sayfa {page} alınamadı, döngü durduruluyor.", flush=True)
            break

        soup = BeautifulSoup(response.text, "html.parser")
        anime_blocks = soup.select("div.list-movie")

        if not anime_blocks:
            print(f"Sayfa {page} içinde anime bulunamadı, döngü durduruluyor.", flush=True)
            break

        page_names = []
        for block in anime_blocks:
            link_tag = block.find("a", class_="list-title")
            if not link_tag:
                link_tag = block.find("a", class_="list-titlesub")
            if not link_tag:
                continue

            href = link_tag.get("href")
            if not href:
                continue

            group = link_tag.text.strip().upper()
            page_names.append(group)

            anime_data[href] = {
                "group": group,
                "last_season": 1,
                "last_episode": 0,
                "start_episode": 1
            }

        for name in page_names:
            print(f"  - {name}", flush=True)

        page += 1
        time.sleep(1)

    total_pages = page - 1
    print(f"\nToplam {total_pages} sayfa gezildi.", flush=True)
    return anime_data, total_pages

def save_to_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Veri '{filename}' dosyasına kaydedildi.", flush=True)

if __name__ == "__main__":
    start_url = "https://izle.animeizlesene.com/series?filter=null"
    result, total_pages = scrape_until_no_more_links(start_url)

    print("\n--- SONUÇ ---")
    print(f"Toplam Sayfa: {total_pages}")
    save_to_json("diziler.json", result)

