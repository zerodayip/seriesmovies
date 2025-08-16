from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://webteizle.info"

# ---- Ortak header'lar ----
COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://webteizle.info",
}


def get_embed_links(movie_url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # debug için False yapabilirsin
        page = browser.new_page()

        print(f"[+] Açılıyor: {movie_url}")
        page.goto(movie_url)
        page.wait_for_timeout(5000)

        # ---- HTML içinden film id çek ----
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        film_id_tag = soup.find("input", {"id": "filmid"})
        if not film_id_tag:
            print("[-] Film ID bulunamadı!")
            browser.close()
            return []

        film_id = film_id_tag.get("value")
        print("[+] Film ID:", film_id)

        embed_links = []

        # ---- Dublaj / Altyazı dene ----
        for dil in ["Dublaj", "Altyazı"]:
            print("[*] Deneniyor:", dil)

            resp = page.request.post(
                f"{BASE_URL}/ajax/dataAlternatif3.asp",
                data={"filmid": film_id, "dil": dil},
                headers={**COMMON_HEADERS, "Referer": movie_url},
            )

            try:
                alternatifler = resp.json()
            except Exception:
                print("[-] JSON parse edilemedi:", resp.text())
                continue

            if not alternatifler:
                print("[-] Hiç alternatif dönmedi.")
                continue

            for alt in alternatifler:
                pid = alt.get("ID")
                if not pid:
                    continue

                # ikinci request → embed iframe
                r2 = page.request.post(
                    f"{BASE_URL}/ajax/dataEmbed.asp",
                    data={"id": pid},
                    headers={**COMMON_HEADERS, "Referer": movie_url},
                )

                try:
                    data = r2.json()
                except Exception:
                    print("[-] Embed JSON parse hatası:", r2.text())
                    continue

                link = data.get("Link")
                if link:
                    print("[EMBED]", link)
                    embed_links.append(link)

        browser.close()
        return embed_links


if __name__ == "__main__":
    url = "https://webteizle.info/izle/altyazi/ne-zha-2"
    links = get_embed_links(url)
    print("\n==== Tüm Bulunan Embedler ====")
    for l in links:
        print(l)
