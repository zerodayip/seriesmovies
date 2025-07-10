import requests

BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...."  # Kendi tokenini buraya koy
CHANNELS_URL = "https://core-api.kablowebtv.com/api/channels/all"

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://tvheryerde.com",
    "Origin": "https://tvheryerde.com"
}

def main():
    try:
        res = requests.get(CHANNELS_URL, headers=HEADERS, timeout=20)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"[!] API Hatası: {e}")
        return

    all_channels = data.get("Data", {}).get("AllChannels", [])
    if not all_channels:
        print("Kanal bulunamadı.")
        return

    print(f"Tüm kanallar ({len(all_channels)} adet):\n")
    for i, ch in enumerate(all_channels, 1):
        uuid = ch.get("UId", "YOK")
        name = ch.get("Name", "YOK")
        logo = ch.get("PrimaryLogoImageUrl", "YOK")
        stream_data = ch.get("StreamData")
        if stream_data and isinstance(stream_data, dict):
            stream_url = stream_data.get("DashStreamUrl", "YOK")
            drm = stream_data.get("IsDrmEnabled", False)
        else:
            stream_url = "YOK"
            drm = False
        print(f"{i}. Kanal")
        print(f"   ID       : {uuid}")
        print(f"   İsim     : {name}")
        print(f"   Logo     : {logo}")
        print(f"   Stream   : {stream_url}")
        print(f"   DRM      : {'VAR' if drm else 'YOK'}")
        print("------")

if __name__ == "__main__":
    main()

