import asyncio
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.showtv.com.tr"
LIST_URL = f"{BASE_URL}/diziler"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

async def fetch_list(client):
    r = await client.get(LIST_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    shows = []
    for box in soup.select('div[data-name="box-type6"]'):
        link_tag = box.select_one("a.group")
        img_tag = box.select_one("img")
        name_tag = box.select_one("figcaption span")

        link = BASE_URL + link_tag.get("href", "").strip() if link_tag else ""
        img_url = img_tag.get("src", "").strip() if img_tag else ""
        name = name_tag.get_text(strip=True) if name_tag else ""

        shows.append({"name": name, "link": link, "img": img_url})
    return shows

async def fetch_details(show, client):
    try:
        r = await client.get(show["link"])
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Bölüm listesi (ilk bölümden son bölüme sıralı)
        episodes = []
        for opt in soup.select('#seasonWithJs option[data-href]'):
            bolum_no = opt.text.strip()
            bolum_link = BASE_URL + opt.get("data-href").strip()
            episodes.append({"bolum": bolum_no, "link": bolum_link})

        episodes.reverse()  # Eski → yeni sıralama
        show["episodes"] = episodes

    except Exception as e:
        show["episodes"] = [{"bolum": "Hata", "link": str(e)}]
    return show

async def main():
    transport = httpx.AsyncHTTPTransport(retries=3, local_address="0.0.0.0")
    async with httpx.AsyncClient(headers=HEADERS, timeout=20, transport=transport) as client:
        shows = await fetch_list(client)
        tasks = [fetch_details(show, client) for show in shows]
        results = await asyncio.gather(*tasks)

    for s in results:
        print(f"Ad: {s['name']}")
        print(f"Resim: {s['img']}")
        for ep in s.get("episodes", []):
            print(f"  {ep['bolum']}: {ep['link']}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
