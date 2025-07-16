import os
import requests
import base64

GH_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def fetch_large_file(owner, repo, path, branch):
    # 1. Önce SHA'yı al
    url1 = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    res1 = requests.get(url1, headers=HEADERS)
    res1.raise_for_status()
    data1 = res1.json()
    if "sha" not in data1:
        raise Exception(f"SHA bulunamadı! keys: {data1.keys()}")
    sha = data1["sha"]

    # 2. Sonra blob içeriğini al
    url2 = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}"
    res2 = requests.get(url2, headers=HEADERS)
    res2.raise_for_status()
    data2 = res2.json()
    content = base64.b64decode(data2["content"]).decode("utf-8").splitlines()
    return content

if __name__ == "__main__":
    dizigom_lines = fetch_large_file(
        "zerodayip", "dizigom", "dizigomdizi.m3u", "main"
    )
    print("== Dizigom İlk 5 Satır ==")
    for line in dizigom_lines[:5]:
        print(line)

    sezonluk_lines = fetch_large_file(
        "zerodayip", "sezonlukdizi", "sezonlukdizi.m3u", "main"
    )
    print("\n== Sezonlukdizi İlk 5 Satır ==")
    for line in sezonluk_lines[:5]:
        print(line)
