import requests
from bs4 import BeautifulSoup
import re
import time

def get_embed_links(episode_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
    }

    print(f"Loading episode page: {episode_url}")
    res = requests.get(episode_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Find all hoster list elements
    hoster_list = soup.select("div.hosterSiteVideo ul li")
    if not hoster_list:
        print("No hosters found!")
        return

    print(f"Found {len(hoster_list)} hosters.")

    for hoster in hoster_list:
        hoster_name = hoster.select_one("h4")
        name = hoster_name.text.strip() if hoster_name else "Unknown"
        if name.lower() == "vidoza":
            continue  # skip vidoza as in original code

        # Each hoster has a data-link-target attribute (redirect link)
        hoster_link = hoster.get("data-link-target")
        if not hoster_link:
            continue

        # Go to the hoster redirect page (it usually redirects to the real embed link)
        hoster_page_url = requests.compat.urljoin(episode_url, hoster_link)
        print(f"\nHoster: {name}")
        print(f"  Redirect page: {hoster_page_url}")

        hoster_res = requests.get(hoster_page_url, headers=headers, allow_redirects=True)
        # Final URL after all redirects (usually the embed link!)
        real_embed_url = hoster_res.url

        # Try to find an iframe (optional, for more reliability)
        hoster_soup = BeautifulSoup(hoster_res.text, "html.parser")
        iframe = hoster_soup.find("iframe")
        if iframe and iframe.get("src"):
            print(f"  Embed iframe: {iframe['src']}")
        else:
            # Or print the final redirected URL (often works for VOE, Doodstream, Streamtape, etc.)
            print(f"  Embed link: {real_embed_url}")

if __name__ == "__main__":
    # Example episode link (change this to a real episode URL)
    episode_url = "https://aniworld.to/anime/stream/from-old-country-bumpkin-to-master-swordsman"  # <-- change to a real episode url!
    get_embed_links(episode_url)
