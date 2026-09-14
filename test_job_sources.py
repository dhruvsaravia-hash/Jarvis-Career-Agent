from job_sources import search_indeed

print("="*60)
print("JARVIS JOB SOURCE TEST")
print("="*60)

jobs = search_indeed(
    "python internship",
    "mumbai"
)

print("\nTotal Jobs:", len(jobs))

for index, job in enumerate(jobs[:10], start=1):
    print(f"\n--- JOB {index} ---", job)