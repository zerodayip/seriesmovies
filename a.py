from playwright.sync_api import sync_playwright
import sys

def get_real_download_link(mediafire_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # test için görünür aç
        context = browser.new_context()
        page = context.new_page()
        found = None

        def handle_response(response):
            print("URL:", response.url)
            if (
                response.url.startswith("https://download")
                and "mediafire.com" in response.url
                and (
                    response.url.endswith(".mp4")
                    or response.url.endswith(".mkv")
                    or response.url.endswith(".zip")
                    or response.url.endswith(".rar")
                )
            ):
                nonlocal found
                found = response.url

        page.on("response", handle_response)
        page.goto(mediafire_url)
        page.wait_for_selector("a#downloadButton", timeout=20000)
        btn = page.query_selector("a#downloadButton")
        if btn:
            dkey_link = btn.get_attribute("href")
            if dkey_link.startswith("//"):
                dkey_link = "https:" + dkey_link
            elif dkey_link.startswith("/"):
                dkey_link = "https://www.mediafire.com" + dkey_link
            print("Dkey link:", dkey_link)
            with page.expect_popup() as popup_info:
                btn.click()
            popup = popup_info.value
            popup.on("response", handle_response)
            popup.wait_for_timeout(15000)
        else:
            print("Download butonu bulunamadı!")
            browser.close()
            return

        if found:
            print("Gerçek download link:", found)
        else:
            print("Gerçek download link bulunamadı!")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python mediafire_all_playwright.py <mediafire-page-link>")
        sys.exit(1)
    get_real_download_link(sys.argv[1])
