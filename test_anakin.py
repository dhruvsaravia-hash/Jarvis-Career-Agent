import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANAKIN_API_KEY")
BASE_URL = "https://api.anakin.io"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}

response = requests.get(
    f"{BASE_URL}/v1/wire/search",
    headers=headers,
    params={
        "q": "search jobs",
        "auth": "false",
    },
    timeout=30,
)

print("STATUS:", response.status_code)
print()
print("RESPONSE:")
print(response.text)
