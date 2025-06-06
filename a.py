import requests
import re
from bs4 import BeautifulSoup

def get_embed_links(video_page_url):
    # 1. Video sayfasını çek
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
    }
    resp = requests.get(video_page_url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    # 2. .parilda elementlerinden data-embed id'lerini topla
    parilda_elements = soup.select(".parilda")
    embed_ids = [el.get("data-embed") for el in parilda_elements if el.get("data-embed")]

    embed_links = []

    # 3. Her bir embed id için POST isteği atıp iframe src'sini al
    for embed_id in embed_ids:
        post_url = "https://www.animeizlesene.com/ajax/embed"
        post_headers = {
            "User-Agent": headers["User-Agent"],
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.animeizlesene.com",
            "Referer": video_page_url,
        }
        post_data = {"id": embed_id}

        post_resp = requests.post(post_url, data=post_data, headers=post_headers, verify=False)
        # 4. Regex ile src="..." kısımlarını bul
        matches = re.findall(r'src="([^"]+)"', post_resp.text)
        for url in matches:
            # // ile başlıyorsa https ekle
            if url.startswith("//"):
                url = "https:" + url
            embed_links.append(url)

    return embed_links

# Örnek kullanım:
if __name__ == "__main__":
    video_url = "https://www.animeizlesene.com/serie/kusuriya-no-hitorigoto-484-2-season-21-episode"  # Buraya bir anime bölümü linki koy
    links = get_embed_links(video_url)
    for i, link in enumerate(links, 1):
        print(f"{i}. {link}")
