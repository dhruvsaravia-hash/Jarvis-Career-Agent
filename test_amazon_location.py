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


payload = {
    "action_id": "act_amazon_jobs_job_search_listing",

    "params": {
        "query": "python internship",
        "start": 0,
        "size": 10,

        "filter_facets": [
            {
                "name": "category",
                "values": [
                    {
                        "name": "Software Development"
                    }
                ],
                "requestedFacetCount": 9999
            }
        ],

        "location_facets": [
            [
                {
                    "name": "country",
                    "requestedFacetCount": 9999
                },
                {
                    "name": "normalizedStateName",
                    "requestedFacetCount": 9999
                },
                {
                    "name": "normalizedCityName",
                    "requestedFacetCount": 9999
                }
            ]
        ],

        "job_type_facets": [],

        "sort": {
            "sortType": "SCORE",
            "sortOrder": "DESCENDING"
        }
    }
}


print("[TEST] Creating Amazon location task...")

response = requests.post(
    f"{BASE_URL}/v1/wire/task",
    headers=headers,
    json=payload,
    timeout=30
)

print("CREATE STATUS:", response.status_code)
print("CREATE RESPONSE:", response.text)

if response.status_code != 202:
    raise RuntimeError("Task creation failed")

job_id = response.json()["job_id"]

print("\n[TEST] Job ID:", job_id)

for i in range(30):

    response = requests.get(
        f"{BASE_URL}/v1/wire/jobs/{job_id}",
        headers=headers,
        timeout=30
    )

    result = response.json()

    print(f"\n[TEST] Poll {i + 1}:")
    print(result)

    status = result.get("status")

    if status in ("completed", "succeeded"):

        print("\n========== SUCCESS ==========")

        data = (
            result
            .get("data", {})
            .get("data", {})
        )

        items = data.get("items", [])

        print("\nJOBS FOUND:", len(items))

        for index, item in enumerate(items, start=1):

            print(f"\n--- JOB {index} ---")
            print(item)

        break

    if status in ("failed", "error"):

        print("\n========== FAILED ==========")
        print(result)

        break

    time.sleep(2)

else:

    print("\n========== TIMEOUT ==========")
