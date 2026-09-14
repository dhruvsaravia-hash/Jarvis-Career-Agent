import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANAKIN_API_KEY")
BASE_URL = "https://api.anakin.io"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}

# Create Indeed search task
payload = {
    "action_id": "in_search_jobs",
    "params": {
        "query": "python internship",
        "location": "Mumbai",
        "start": 0,
        "sort": "relevance",
        "country_domain": "in",
    },
}

print("[TEST] Creating Indeed task...")

response = requests.post(
    f"{BASE_URL}/v1/wire/task",
    headers=headers,
    json=payload,
    timeout=30,
)

print("CREATE STATUS:", response.status_code)
print("CREATE RESPONSE:", response.text)

response.raise_for_status()

job_id = response.json().get("job_id")

if not job_id:
    raise RuntimeError("No job_id returned")

print("[TEST] Job ID:", job_id)

# Poll task
poll_url = f"{BASE_URL}/v1/wire/jobs/{job_id}"

for i in range(30):

    response = requests.get(
        poll_url,
        headers=headers,
        timeout=30,
    )

    print(f"[TEST] Poll {i + 1}:", response.status_code)

    result = response.json()

    print(result)

    status = result.get("status")

    if status in ("completed", "succeeded"):
        print("\nSUCCESS!")
        break

    if status in ("failed", "error"):
        print("\nFAILED!")
        break

    time.sleep(2)
else:
    print("\nTimed out waiting for Anakin.")
