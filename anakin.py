import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ANAKIN_API_KEY = os.getenv("ANAKIN_API_KEY")
BASE_URL = "https://api.anakin.io"


def get_headers():
    if not ANAKIN_API_KEY:
        raise RuntimeError("ANAKIN_API_KEY is missing. Check your .env file.")

    return {
        "X-API-Key": ANAKIN_API_KEY,
        "Content-Type": "application/json",
    }


def get_job_search_action():
    response = requests.get(
        f"{BASE_URL}/v1/wire/search",
        headers=get_headers(),
        params={
            "q": "search jobs",
            "auth": "false",
        },
        timeout=30,
    )
    response.raise_for_status()

    results = response.json().get("results", [])

    action = next((item for item in results if item["action_id"] == "in_search_jobs"), None)
    
    if action is None:
        raise RuntimeError("Anakin did not return the Indeed job-search action: in_search_jobs")
    return action


def search_jobs(query, location):
    action = get_job_search_action()

    payload = {
        "action_id": action["action_id"],
        "params": {
            "query": query,
            "location": location,
            "start": 0,
            "sort": "relevance",
            "country_domain": "in",
        },
    }

    print(f"[JARVIS] Using action: {payload['action_id']}")

    response = requests.post(
        f"{BASE_URL}/v1/wire/task",
        headers=get_headers(),
        json=payload,
        timeout=30,
    )

    if response.status_code != 202:
        try:
            error = response.json()
        except ValueError:
            error = response.text
        raise RuntimeError(f"Anakin API Error ({response.status_code}): {error}")

    job_id = response.json().get("job_id")

    if not job_id:
        raise RuntimeError("Anakin did not return a job_id.")

    print(f"[JARVIS] Anakin job created: {job_id}")

    poll_url = f"{BASE_URL}/v1/wire/jobs/{job_id}"

    while True:
        response = requests.get(
            poll_url,
            headers=get_headers(),
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"Anakin polling error ({response.status_code}): {response.text}"
            )

        result = response.json()
        status = result.get("status")
        print("Status:", status)

        if status in ("completed", "succeeded"):
            return result

        if status in ("failed", "error"):
            raise RuntimeError(f"Anakin task failed: {result}")

        time.sleep(2)