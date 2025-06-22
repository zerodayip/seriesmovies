import sys
sys.stdout.reconfigure(line_buffering=True)

from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

PROXY_PREFIX = "https://zeroipday-zeroipday.hf.space/proxy/vctplay?url="
OUTPUT_FILE = "setfilmizlefilm.txt"

def get_fastplay_embeds_bs(film_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": film_url,
    }
    embeds = []
    try:
        resp = requests.get(film_url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        playex_div = soup.select_one("div#playex")
        nonce = playex_div.get("data-nonce") if playex_div else None
        if not nonce:
            return []
        for btn in soup.select('nav.player a, .idTabs.sourceslist a'):
            if btn.get("data-player-name", "").lower() == "fastplay":
                post_id = btn.get("data-post-id")
                part_key = btn.get("data-part-key", "")
                b_tag = btn.find("b")
                label_main = b_tag.get_text(strip=True) if b_tag else (btn.get_text(strip=True) or "FastPlay")
                if part_key and "dublaj" in part_key.lower():
                    label = "Türkçe Dublaj"
                elif part_key and "altyazi" in part_key.lower():
                    label = "Türkçe Altyazılı"
                elif not part_key:
                    label = "Türkçe Altyazılı"
                else:
                    label = label_main
                payload = {
                    "action": "get_video_url",
                    "nonce": nonce,
                    "post_id": post_id,
                    "player_name": "FastPlay",
                    "part_key": part_key
                }
                ajax_headers = {
                    "User-Agent": "Mozilla/5.0",
                    "Referer": film_url,
                    "X-Requested-With": "XMLHttpRequest"
                }
                r = requests.post("https://www.setfilmizle.nl/wp-admin/admin-ajax.php", data=payload, headers=ajax_headers, timeout=15)
                try:
                    data = r.json()
                    embed_url = data.get("data", {}).get("url")
                    if embed_url:
                        embeds.append((label, embed_url))
                except Exception:
                    pass
        return embeds
    except Exception:
        return []

def fetch_embed_info(film_info):
    title, rating, anayil, film_link, logo_url = film_info
    fastplay_embeds = get_fastplay_embeds_bs(film_link)
    return (title, fastplay_embeds)

def gather_film_infos(page):
    articles = page.query_selector_all("article.item.dortlu.movies")
    film_infos = []
    for art in articles:
        title = art.query_selector("h2")
        title_text = title.inner_text().strip() if title else "?"
        film_link = art.query_selector(".poster a").get_attribute("href")
        logo_url = ""
        film_infos.append((title_text, None, None, film_link, logo_url))
    return film_infos

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.setfilmizle.nl/film/")
    page.wait_for_selector("article.item.dortlu.movies")
    print("İlk sayfa yüklendi.", flush=True)

    # Kaç sayfa var?
    try:
        element = page.query_selector("span.last-page")
        if element:
            max_page = int(element.get_attribute("data-page"))
        else:
            all_numbers = [int(e.get_attribute("data-page")) for e in page.query_selector_all("span.page-number") if e.get_attribute("data-page") and e.get_attribute("data-page").isdigit()]
            max_page = max(all_numbers) if all_numbers else 1
    except Exception:
        max_page = 1

    print(f"Toplam sayfa: {max_page}", flush=True)

    all_film_infos = []
    for current_page in range(1, max_page + 1):
        if current_page > 1:
            page.click(f"span.page-number[data-page='{current_page}']")
            time.sleep(1)
        film_infos = gather_film_infos(page)
        print(f"{current_page}. sayfa film sayısı: {len(film_infos)}", flush=True)
        all_film_infos.extend(film_infos)

    browser.close()

    print(f"Toplam film bulundu: {len(all_film_infos)}", flush=True)
    print(f"Tüm filmler embed linkleri ile {OUTPUT_FILE} dosyasına yazılıyor...", flush=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fout:
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_film = {executor.submit(fetch_embed_info, info): info for info in all_film_infos}
            for future in as_completed(future_to_film):
                title, fastplay_embeds = future.result()
                if fastplay_embeds:
                    for label, emb_url in fastplay_embeds:
                        line = f"Film: {title} | {label} | EMBED: {PROXY_PREFIX + emb_url}"
                        print(line, flush=True)
                        fout.write(line + "\n")
                else:
                    line = f"Film: {title} | FastPlay embed bulunamadı!"
                    print(line, flush=True)
                    fout.write(line + "\n")

    print("Tamamlandı! ✅", flush=True)
