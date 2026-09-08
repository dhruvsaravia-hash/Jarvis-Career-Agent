from anakin import search_jobs
from matcher import calculate_match

def main():
    print("="*60)
    print("          JARVIS CAREER AGENT")
    print("="*60)

    query = input("What type of job are you looking for?")
    location = input("Location: ")

    try:
        
        result = search_jobs(query, location)

        jobs = (result.get("data", {}).get("data", {}).get("jobs", []))
        
        if not jobs:
            print("[JARVIS] No jobs found.")
            return
        
        print(f"[JARVIS] found {len(jobs)} jobs.\n")
        
        analyzed_jobs = []
        
        for job in jobs:
            analysis = calculate_match(job)
            analyzed_jobs.append(analysis)
            
        analyzed_jobs = [calculate_match(job) for job in jobs]        
        analyzed_jobs.sort(key=lambda x: x["score"], reverse=True)
            
        print("=" * 60)
        print("              TOP JOB MATCHES")
        print("=" * 60)
            
        for index, job in enumerate(analyzed_jobs[:10], start=1):
            print(f"\n#{index} {job['title']}")
            print(f"Company: {job['company']}")
            print(f"Location: {job['location']}")
            print(f"Match: {job['score']}%")
            print("Matched:", ", ".join(job["matched_skills"]) if job["matched_skills"] else "None")
            print("Missing:", ", ".join(job["missing_skills"]) if job["missing_skills"] else "None")
            print(f"url:{job['url']}")
        
    except Exception as e:
        print("\n[JARVIS ERROR]", e)   
        
if __name__ == "__main__":
    main()         