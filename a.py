import os
import requests
import re
import base64

GH_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def fetch_large_file(owner, repo, path, branch):
    url1 = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    res1 = requests.get(url1, headers=HEADERS)
    res1.raise_for_status()
    data1 = res1.json()
    if "sha" not in data1:
        raise Exception(f"SHA bulunamadı! keys: {data1.keys()}")
    sha = data1["sha"]
    url2 = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}"
    res2 = requests.get(url2, headers=HEADERS)
    res2.raise_for_status()
    data2 = res2.json()
    content = base64.b64decode(data2["content"]).decode("utf-8").splitlines()
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
    print("Dizigom m3u indiriliyor...")
    dizi_lines = fetch_large_file(
        "zerodayip", "dizigom", "dizigomdizi.m3u", "main"
    )
    print("Sezonlukdizi m3u indiriliyor...")
    sezonluk_lines = fetch_large_file(
        "zerodayip", "sezonlukdizi", "sezonlukdizi.m3u", "main"
    )

    dizi_entries = parse_m3u_lines(dizi_lines)
    sezon_entries = parse_m3u_lines(sezonluk_lines)
    merged = ["#EXTM3U"]
    yazilan_set = set()  # (tvg-id, tvg-name, mode)
    atlananlar = []

    # Dizigom başa eklenir
    for entry in dizi_entries:
        extinf = entry[0]
        tvg_id, tvg_name, mode = get_tvgid_tvgname_mode(extinf)
        key = (tvg_id, tvg_name, mode)
        if key not in yazilan_set:
            merged.extend(entry)
            yazilan_set.add(key)

    # Sezonlukdizi'den sadece eksik olanlar eklenir, eklenmeyenler atlananlar'a
    for entry in sezon_entries:
        extinf = entry[0]
        tvg_id, tvg_name, mode = get_tvgid_tvgname_mode(extinf)
        key = (tvg_id, tvg_name, mode)
        # DEBUG
        print("[SEZONLUK]", key, "| Mode:", mode)
        if key not in yazilan_set:
            print("[EKLENEN]", key, extinf)
            merged.extend(entry)
            yazilan_set.add(key)
        else:
            print("[ATLANAN]", key, extinf)
            atlananlar.append(entry)

    # Dosyaya yaz
    with open("merged_output.m3u", "w", encoding="utf-8") as f:
        for line in merged:
            if isinstance(line, list):
                for sub in line:
                    f.write(sub + "\n")
            else:
                f.write(line + "\n")
    print("merged_output.m3u başarıyla oluşturuldu.")

    print("\n--- Atlanan veriler ---")
    for entry in atlananlar:
        print("\n".join(entry))
        print("-" * 40)

if __name__ == "__main__":
    main()
