from playwright.sync_api import sync_playwright
import time

# Dizi sayfasının URL'si
film_url = "https://www.setfilmizle.nl/dizi/the-sympathizer/"

def get_part_keys_with_playwright(film_url):
    with sync_playwright() as p:
        # Chromium tarayıcısını başlatıyoruz
        browser = p.chromium.launch(headless=False)  # headless=False ile tarayıcıyı görebilirsiniz
        page = browser.new_page()
        page.goto(film_url)

        # Sayfanın tamamen yüklenmesini bekliyoruz (belirli bir öğe görünene kadar)
        page.wait_for_selector("div#seasons")  # Bu selector, sezonların bulunduğu öğeyi bekliyor

        # Sezonlar ve bölümler
        sezonlar = page.query_selector_all("div#seasons div.se-c")

        for sezon in sezonlar:
            sezon_adi = sezon.query_selector("h3.title").inner_text().strip()
            print(f"\n{sezon_adi}")

            bolumler = sezon.query_selector_all("ul.episodios li")
            for bolum in bolumler:
                bolum_adi = bolum.query_selector("h4.episodiotitle a").inner_text().strip()
                bolum_link = bolum.query_selector("a").get_attribute("href")
                print(f"{bolum_adi} - {bolum_link}")

                # FastPlay butonlarını alıyoruz
                fastplay_buttons = bolum.query_selector_all("a[data-player-name='FastPlay']")
                
                # Eğer FastPlay butonları varsa, part-key'lerini alıyoruz
                part_keys = []
                for fastplay_btn in fastplay_buttons:
                    part_key = fastplay_btn.get_attribute("data-part-key")
                    if part_key:
                        part_keys.append(part_key)

                if part_keys:
                    print(f"Part Keys: {', '.join(part_keys)}")
                else:
                    print("Hiçbir part-key bulunamadı.")

                # Bölüm linkine gidiyoruz ve 2 saniye bekliyoruz
                time.sleep(2)  # 2 saniye bekleme

                # Bölüm sayfasına gidip embed linkini almak için AJAX isteği atmamız gerekiyor
                bolum_resp = page.goto(bolum_link)
                page.wait_for_selector("div#playex")  # Playex öğesinin görünmesini bekliyoruz

                # AJAX isteğini almak için gerekli parametreleri almak
                playex_div = page.query_selector("div#playex")
                nonce = playex_div.get_attribute("data-nonce") if playex_div else None
                if not nonce:
                    print("Nonce bulunamadı!")
                    continue

                fastplay_btn = None
                for btn in page.query_selector_all("nav.player a"):
                    if btn.get_attribute("data-player-name").lower() == "fastplay":
                        fastplay_btn = btn
                        break

                if not fastplay_btn:
                    print("FastPlay player bulunamadı!")
                    continue

                post_id = fastplay_btn.get_attribute("data-post-id")
                part_key = fastplay_btn.get_attribute("data-part-key")

                # Payload'u hazırlıyoruz
                payload = {
                    "action": "get_video_url",
                    "nonce": nonce,
                    "post_id": post_id,
                    "player_name": "FastPlay",
                    "part_key": part_key
                }

                # AJAX isteğini gönderiyoruz
                response = page.request.post(
                    "https://www.setfilmizle.nl/wp-admin/admin-ajax.php",
                    data=payload
                )

                try:
                    data = response.json()
                    embed_url = data.get("data", {}).get("url")
                    if embed_url:
                        print(f"Embed Linki: {embed_url}")
                    else:
                        print(f"Embed linki bulunamadı! JSON: {data}")
                except Exception as e:
                    print(f"JSON parsing error: {e}")

        browser.close()

# Fonksiyonu çalıştır
get_part_keys_with_playwright(film_url)

