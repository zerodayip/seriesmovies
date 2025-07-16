import os
import requests
import re
import base64

# ENV: GH_TOKEN otomatik geliyor (workflow veya shell ortamı)
GH_TOKEN = os.getenv("GH_TOKEN")

# Repo bilgiler
DIZIGOM_OWNER = "zerodayip"
DIZIGOM_REPO = "dizigom"
DIZIGOM_PATH = "dizigomdizi.m3u"
DIZIGOM_BRANCH = "main"

SEZONLUK_OWNER = "zerodayip"
SEZONLUK_REPO = "sezonlukdizi"
SEZONLUK_PATH = "sezonlukdizi.m3u"
SEZONLUK_BRANCH = "main"

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

def parse_m3u_lines(lines):
    entries = []
    entry = []
    for line in lines:
        if line.startswith("#EXTINF"):
            entry = [line]
        elif line.startswith("http"):
            if entry:
                entry.append(line)
                entries.append(entry)
                entry = []
    return entries

def get_tvgid_tvgname_mode(extinf_line):
    tvg_id_match = re.search(r'tvg-id="([^"]+)"', extinf_line)
    tvg_id = tvg_id_match.group(1) if tvg_id_match else ""
    tvg_name_match = re.search(r'tvg-name="([^"]+)"', extinf_line)
    tvg_name = tvg_name_match.group(1) if tvg_name_match else ""
    title = extinf_line.split(",", 1)[-1].strip().upper()
    if "DUBLAJ" in title:
        mode = "DUBLAJ"
    elif "ALTYAZI" in title:
        mode = "ALTYAZI"
    else:
        mode = "DİĞER"
    return tvg_id, tvg_name, mode

def main():
    # 1) Dosyaları çek
    print("Dizigom m3u indiriliyor...")
    dizi_lines = fetch_file_from_github(DIZIGOM_OWNER, DIZIGOM_REPO, DIZIGOM_PATH, DIZIGOM_BRANCH)
    print("Sezonlukdizi m3u indiriliyor...")
    sezon_lines = fetch_file_from_github(SEZONLUK_OWNER, SEZONLUK_REPO, SEZONLUK_PATH, SEZONLUK_BRANCH)

    # 2) Parse et
    dizi_entries = parse_m3u_lines(dizi_lines)
    sezon_entries = parse_m3u_lines(sezon_lines)
    merged = ["#EXTM3U"]
    yazilan_set = set()  # (tvg-id, tvg-name, mode)

    # 3) dizigomdizi.m3u başa
    for entry in dizi_entries:
        extinf = entry[0]
        tvg_id, tvg_name, mode = get_tvgid_tvgname_mode(extinf)
        key = (tvg_id, tvg_name, mode)
        if key not in yazilan_set:
            merged.extend(entry)
            yazilan_set.add(key)

    # 4) sezonlukdizi.m3u'dan eksik olanlar
    for entry in sezon_entries:
        extinf = entry[0]
        tvg_id, tvg_name, mode = get_tvgid_tvgname_mode(extinf)
        key = (tvg_id, tvg_name, mode)
        if key not in yazilan_set:
            merged.extend(entry)
            yazilan_set.add(key)

    # 5) Dosyaya yaz
    with open("merged_output.m3u", "w", encoding="utf-8") as f:
        for line in merged:
            if isinstance(line, list):
                for sub in line:
                    f.write(sub + "\n")
            else:
                f.write(line + "\n")
    print("merged_output.m3u başarıyla oluşturuldu.")

if __name__ == "__main__":
    main()
