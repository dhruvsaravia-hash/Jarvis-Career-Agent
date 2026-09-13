import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANAKIN_API_KEY")
BASE_URL = "https://api.anakin.io"

HEADERS = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json",
}

def run_anakin_action(action_id, params):
    payload = {
        "action_id": action_id,
        "params": params
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/wire/task",
        headers=HEADERS,
        json=payload,
        timeout=30
    )
    
    if response.status_code != 202:
        print("[ANAKIN] Task creation failed: ")
        print(response.text)
        return []
    
    job_id = response.json()["job_id"]
    
    print(f"[ANAKIN] Task started: {action_id}")
    print(f"[ANAKIN] Job ID: {job_id}")  
    
    for i in range(30):
        time.sleep(2)
        
        response = requests.get(
            f"{BASE_URL}/v1/wire/jobs/{job_id}",
            headers=HEADERS,
            timeout=30
        )          
        
        result = response.json()
        
        status = result.get("status")
        
        print(f"[ANAKIN] Poll {i + 1}: {status}")
        
        if status == "completed":
            data = (
                result
                .get("data", {})
                .get("data", {})
            )
            
            return data.get("items", [])
        
        if status in ("failed", "error"):
            print("[ANAKIN] Task failed: ", result)
            return []
        
    print("[ANAKIN] Task timed out.")
    return []

def search_indeed(query, location):
    
    return run_anakin_action(
        "in_search_jobs",
        {
            "query": query,
            "location": location,
            "start": 0,
            "sort": "relevance",
            "country_domain": "in"
        }
    )    