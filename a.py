from playwright.sync_api import sync_playwright
import re
import json

BASE_URL = "https://webteizle.info"

def get_embed_links(url):
    results = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=60000)

        film_id = page.get_attribute("button#wip", "data-id")
        if not film_id:
            print("Film ID bulunamadı!")
            return []

        print(f"[+] Film ID: {film_id}")

        for dil, dil_name in [("0", "Dublaj"), ("1", "Altyazı")]:
            resp = page.request.post(
                f"{BASE_URL}/ajax/dataAlternatif3.asp",
                data={"filmid": film_id, "dil": dil},
                headers={"Referer": url}
            )
            if resp.status != 200:
                continue

            try:
                players = resp.json()
            except:
                continue

            for player in players:
                pid = str(player.get("id"))
                pname = player.get("name", "Bilinmeyen")

                r2 = page.request.post(
                    f"{BASE_URL}/ajax/dataEmbed.asp",
                    data={"id": pid},
                    headers={"Referer": url}
                )

                if r2.status != 200:
                    continue

                html = r2.text()

                # 1) iframe
                iframe_match = re.search(r'<iframe[^>]+src="([^"]+)"', html)
                if iframe_match:
                    link = iframe_match.group(1)
                    results.append({
                        "dil": dil_name,
                        "player": pname,
                        "url": link
                    })
                    continue

                # 2) bilinen host regex
                vidmoly = re.search(r"vidmoly\.(?:net|to)/embed-([a-zA-Z0-9]+)", html)
                okru = re.search(r"ok.ru/videoembed/(\d+)", html)
                filemoon = re.search(r"filemoon\.sx/e/([a-zA-Z0-9]+)", html)

                if vidmoly:
                    link = f"https://vidmoly.to/embed-{vidmoly.group(1)}.html"
                    results.append({
                        "dil": dil_name,
                        "player": "Vidmoly",
                        "url": link
                    })

                elif okru:
                    link = f"https://ok.ru/videoembed/{okru.group(1)}"
                    results.append({
                        "dil": dil_name,
                        "player": "Okru",
                        "url": link
                    })

                elif filemoon:
                    link = f"https://filemoon.sx/e/{filemoon.group(1)}"
                    results.append({
                        "dil": dil_name,
                        "player": "Filemoon",
                        "url": link
                    })

                # 3) JS encoded kaynak
                enc_match = re.search(r'var\s+\\?"?src\\?"?\s*=\s*"(.*?)"', html)
                if enc_match:
                    raw = enc_match.group(1)
                    try:
                        decoded = raw.encode("utf-8").decode("unicode_escape")
                    except:
                        decoded = raw
                    results.append({
                        "dil": dil_name,
                        "player": pname,
                        "url": decoded
                    })

        browser.close()
    return results


if __name__ == "__main__":
    test_url = "https://webteizle.info/izle/altyazi/ne-zha-2"
    links = get_embed_links(test_url)

    print("\n=== JSON ÇIKTISI ===")
    print(json.dumps(links, indent=2, ensure_ascii=False))
