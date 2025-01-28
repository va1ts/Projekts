import requests
import time

def fetch_room_data(building_id="512"):
    url = "https://co2.mesh.lv/api/device/list"
    payload = {"buildingId": building_id, "captchaToken": None}
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }

    for _ in range(3):  # Retry up to 3 times
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Request error: {e}")
            time.sleep(1)
    return []
