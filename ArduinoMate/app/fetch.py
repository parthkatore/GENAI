import requests

url = "YOUR_ARDUINO_DOCUMENT_URL"

try:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    print(response.text)

except requests.exceptions.RequestException as e:
    print("Download error:", e)