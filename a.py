import requests
from bs4 import BeautifulSoup
import concurrent.futures
import threading

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_free_proxies():
    url = "https://www.sslproxies.org/"
    print("Bedava proxyler çekiliyor...", flush=True)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        proxies = []
        table = soup.find("table", attrs={"id": "proxylisttable"})
        if not table:
            print("Proxy tablosu bulunamadı.", flush=True)
            return proxies
        for row in table.tbody.find_all("tr"):
            cols = row.find_all("td")
            ip = cols[0].text.strip()
            port = cols[1].text.strip()
            https = cols[6].text.strip()
            scheme = "https" if https == "yes" else "http"
            proxies.append(f"{scheme}://{ip}:{port}")
        print(f"{len(proxies)} proxy bulundu.", flush=True)
        return proxies
    except Exception as e:
        print(f"Proxy listesi alınamadı: {e}", flush=True)
        return []

def check_proxy(proxy, test_url="https://animeizlesene.com/series?filter=null"):
    proxies = {"http": proxy, "https": proxy}
    try:
        resp = requests.get(test_url, headers=HEADERS, proxies=proxies, timeout=7)
        if resp.status_code == 200 and "Anime İzle" in resp.text:
            print(f"Çalışan proxy bulundu: {proxy}", flush=True)
            return proxy
    except:
        pass
    return None

def find_working_proxy(proxies, max_workers=20):
    working_proxy = None
    lock = threading.Lock()

    def worker(proxy):
        nonlocal working_proxy
        if working_proxy:
            return None  # Zaten bulundu
        result = check_proxy(proxy)
        if result:
            with lock:
                if not working_proxy:
                    working_proxy = result
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(worker, proxies)

    return working_proxy

def main():
    proxies = get_free_proxies()
    if not proxies:
        print("Proxy bulunamadı, doğrudan bağlantı deneniyor.", flush=True)
        working_proxy = None
    else:
        working_proxy = find_working_proxy(proxies)

    if working_proxy:
        print(f"İlk çalışan proxy: {working_proxy}", flush=True)
        proxies_dict = {"http": working_proxy, "https": working_proxy}
    else:
        print("Çalışan proxy bulunamadı, direkt bağlantı kullanılacak.", flush=True)
        proxies_dict = None

    # Örnek: proxy ile sayfa çekme
    url = "https://animeizlesene.com/series?filter=null"
    try:
        response = requests.get(url, headers=HEADERS, proxies=proxies_dict, timeout=10)
        if response.status_code == 200:
            print("Sayfa başarıyla çekildi, uzunluk:", len(response.text))
            # Burada BeautifulSoup ile parsing yapılabilir
        else:
            print(f"Sayfa çekilirken hata kodu: {response.status_code}")
    except Exception as e:
        print(f"Sayfa çekilirken hata oluştu: {e}")

if __name__ == "__main__":
    main()

