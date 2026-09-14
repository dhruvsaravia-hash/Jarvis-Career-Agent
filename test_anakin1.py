from anakin import search_jobs


print("=" * 60)
print("        JARVIS JOB SEARCH TEST")
print("=" * 60)

query = "python internship"
location = "Mumbai"

print("\n[JARVIS] Query:", query)
print("[JARVIS] Location:", location)

jobs = search_jobs(query, location)

print("\n" + "=" * 60)
print("RESULT")
print("=" * 60)

print("Jobs found:", len(jobs))

for i, job in enumerate(jobs[:5], start=1):

    print(f"\n--- JOB {i} ---")
    print(job)
