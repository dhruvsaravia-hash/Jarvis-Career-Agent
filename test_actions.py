import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANAKIN_API_KEY")

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}

response = requests.get(
    "https://api.anakin.io/v1/wire/search",
    headers=headers,
    params={
        "q": "job search",
        "auth": "false",
    },
    timeout=30,
)

print(response.status_code)

for item in response.json().get("results", []):
    if "job" in (
        item.get("name", "") + " " +
        item.get("catalog_name", "") + " " +
        item.get("description", "")
    ).lower():
        print("\n--------------------")
        print("ACTION ID:", item.get("action_id"))
        print("CATALOG:", item.get("catalog_name"))
        print("NAME:", item.get("name"))
        print("AUTH MODE:", item.get("auth_mode"))
        print("AUTH REQUIRED:", item.get("auth_required"))
        print("PARAMS:", item.get("params"))