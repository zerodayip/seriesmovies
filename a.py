import requests
from bs4 import BeautifulSoup

base_url = "https://aniworld.to"
page_url = "https://aniworld.to/anime/stream/from-old-country-bumpkin-to-master-swordsman"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0 Firefox/101.0"
}

response = requests.get(page_url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

episodes_ul = None
for ul in soup.select("div.hosterSiteDirectNav#stream ul"):
    if ul.find("span") and "Episoden" in ul.find("span").text:
        episodes_ul = ul
        break

episode_links = []
if episodes_ul:
    for a in episodes_ul.find_all("a"):
        abs_link = requests.compat.urljoin(base_url, a.get("href"))
        episode_links.append(abs_link)
else:
    print("Episoden listesi bulunamadı!")

# Her bölüm için çıktı başlığı
for link in episode_links:
    print(f"\nEpisode page: {link}")
    ep_resp = requests.get(link, headers=headers)
    ep_soup = BeautifulSoup(ep_resp.text, "html.parser")

    found = False
    for hoster in ep_soup.select('li[data-lang-key="2"]'):
        hoster_name = hoster.select_one("h4")
        name = hoster_name.text.strip() if hoster_name else "Unknown"
        target = hoster.get("data-link-target")
        if target:
            embed_url = requests.compat.urljoin(base_url, target)
            try:
                r = requests.get(embed_url, headers=headers, allow_redirects=True, timeout=10)
                print(f"  {name}: {r.url}")
                found = True
            except Exception as e:
                print(f"  {name}: (ERROR: {e})")
                found = True
    if not found:
        print("  No English hosters found.")

