import os
import requests
import base64

GH_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def fetch_file_from_github(owner, repo, path, branch):
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    res = requests.get(api_url, headers=HEADERS)
    res.raise_for_status()
    data = res.json()
    if data.get("encoding") == "base64":
        content = base64.b64decode(data["content"]).decode("utf-8").splitlines()
    else:
        content = data["content"].splitlines()
    return content

if __name__ == "__main__":
    # Dizigom
    dizigom_lines = fetch_file_from_github(
        "zerodayip", "dizigom", "dizigomdizi.m3u", "main"
    )
    print("== Dizigom İlk 5 Satır ==")
    for line in dizigom_lines[:5]:
        print(line)

    # Sezonlukdizi
    sezonluk_lines = fetch_file_from_github(
        "zerodayip", "sezonlukdizi", "sezonlukdizi.m3u", "main"
    )
    print("\n== Sezonlukdizi İlk 5 Satır ==")
    for line in sezonluk_lines[:5]:
        print(line)
