from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json
import time

BASE_URL = "https://webteizle.info"

def get_embed_links(movie_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"[+] Açılıyor: {movie_url}")
        page.goto(movie_url)
        page.wait_for_timeout(5000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        # ---- Film ID bul ----
        match = re.search(r"data-filmid=['\"](\d+)['\"]", html)
        if not match:
            print("[!] Film ID bulunamadı")
            return []
        film_id = match.group(1)
        print(f"[+] Film ID: {film_id}")

        # ---- Dil seçeneklerini bul ----
        dil_secimleri = []
        for btn in soup.select(".btn-group .btn"):
            dil = btn.get("data-dil")
            if dil:
                dil_secimleri.append(dil)

        if not dil_secimleri:
            print("[!] Hiç dil seçeneği bulunamadı")
            return []

        print(f"[+] Bulunan diller: {dil_secimleri}")

        all_links = []

        for dil in dil_secimleri:
            print(f"[*] {dil} için linkler alınıyor...")

            response = page.request.post(
                f"{BASE_URL}/ajax/dataAlternatif3.asp",
                headers={"X-Requested-With": "XMLHttpRequest"},
                data={
                    "filmid": film_id,
                    "dil": dil,
                    "s": "",
                    "b": "",
                    "bot": "0"
                }
            )

            text = response.text()
            print(f"    [DEBUG] Response ilk 200 karakter:\n{text[:200]}")

            try:
                player_api = json.loads(text)
            except json.JSONDecodeError:
                print("    [!] JSON parse edilemedi, atlanıyor...")
                continue

            if "data" not in player_api:
                print("    [!] JSON içinde 'data' yok")
                continue

            for item in player_api["data"]:
                link = item.get("link")
                if link:
                    all_links.append((dil, link))

        browser.close()
        return all_links


if __name__ == "__main__":
    movie_url = "https://webteizle.info/izle/altyazi/girlfight"
    links = get_embed_links(movie_url)
    print("\n=== Bulunan Embed Linkler ===")
    for dil, link in links:
        print(f"[{dil}] {link}")
