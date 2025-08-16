import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://webteizle.info"

def get_embed_links(playwright, page_url):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    print(f"[+] Sayfa açılıyor: {page_url}")
    page.goto(page_url)

    # Cloudflare için bekle
    page.wait_for_timeout(8000)

    # Film ID bul
    film_id = page.locator("button#wip").get_attribute("data-id")
    if not film_id:
        print("Film ID bulunamadı!")
        browser.close()
        return []

    print(f"[+] Film ID: {film_id}")

    embed_links = []

    # Hangi dil var?
    dil_list = []
    if page.locator("div.golge a[href*=dublaj]").count() > 0:
        dil_list.append("0")
    if page.locator("div.golge a[href*=altyazi]").count() > 0:
        dil_list.append("1")
    if not dil_list:
        dil_list = ["0", "1"]

    for dil in dil_list:
        print(f"[+] Dil: {'Dublaj' if dil == '0' else 'Altyazı'}")

        # Player listesi isteği
        player_api = page.request.post(
            f"{BASE_URL}/ajax/dataAlternatif3.asp",
            headers={"X-Requested-With": "XMLHttpRequest"},
            data={
                "filmid": film_id,
                "dil": dil,
                "s": "",
                "b": "",
                "bot": "0"
            }
        ).json()

        for embed in player_api.get("data", []):
            embed_id = embed.get("id")
            print(f"   [*] Embed ID: {embed_id}")

            embed_api = page.request.post(
                f"{BASE_URL}/ajax/dataEmbed.asp",
                headers={"X-Requested-With": "XMLHttpRequest"},
                data={"id": str(embed_id)}
            ).text

            soup = BeautifulSoup(embed_api, "html.parser")

            iframe = soup.select_one("iframe")
            if iframe:
                src = iframe.get("src")
                if src and src not in embed_links:
                    embed_links.append(src)
                    print(f"       -> iframe: {src}")
                continue

            # Eğer iframe yoksa script içinden çöz (vidmoly, dzen vs.)
            script = soup.text
            m_vid = re.search(r"""vidmoly\('([\w\d]+)','""", script)
            if m_vid:
                vid_id = m_vid.group(1)
                src = f"https://vidmoly.net/embed-{vid_id}.html"
                if src not in embed_links:
                    embed_links.append(src)
                    print(f"       -> vidmoly: {src}")
                continue

            m_dzen = re.search(r"""var\s+vid\s*=\s*['"]([^'"]+)['"]""", script)
            if m_dzen:
                video_id = m_dzen.group(1)
                src = f"https://dzen.ru/embed/{video_id}"
                if src not in embed_links:
                    embed_links.append(src)
                    print(f"       -> dzen: {src}")

    browser.close()
    return embed_links


if __name__ == "__main__":
    with sync_playwright() as p:
        url = "https://webteizle.info/izle/altyazi/ne-zha-2"
        links = get_embed_links(p, url)

        print("\n[=] Bulunan embed linkleri:")
        for link in links:
            print(link)
