from anakin import search_jobs
from candidate_profile import CANDIDATE_PROFILE
from matcher import (calculate_match, location_matches, build_candidate_from_resume)
from resume_parser import extract_resume_text

class JarvisAgent:
    def __init__(self):
        self.name = "JARVIS"
        
    def run(self, query, location, resume_path="resume.pdf"):
        
        
        print("\n[JARVIS] Understanding your requests...")
        print(f"[JARVIS] job goal: {query}")
        print(f"[JARVIS] preferred location: {location}") 
        
        candidate_profile = {
            "skills": set(),
            "education": "",
            "projects": []
        }
                
        print("\n[JARVIS] Analyzing your resume...")
        
        try:
            resume_text = extract_resume_text(resume_path)
            
            if resume_text.strip():
                print("[JARVIS] Resume loaded successfully.")
                print(f"[JARVIS] Resume text extracted: {len(resume_text)} characters")
                
                candidate_profile = build_candidate_from_resume(resume_text)
                
                print("[JARVIS] skills detected:", ", ".join(sorted(candidate_profile["skills"]))
                      if candidate_profile["skills"] else "None")
                    
                
            else:
                print("[JARVIS] Resume appears to be empty.")
                
        except Exception as e:
            print(f"[JARVIS] Resume analysis failed: {e}")        
        
        plan = [
            "Read and analyze resume",
            "Search live job opportunities",
            "Read job requirements",
            "Compare candidate with each job",
            "Calculate match scores",
            "Rank opportunities",
            "Make final recommendation",
            "Take action with user approval"
        ]       
        
        print("\n[JARVIS] Plan: ")
        for number, step in enumerate(plan, start=1):
            print(f"{number}.{step}")
            
        print("\n" + "-" * 60)
        print("🌐 PHASE 2 — LIVE JOB DISCOVERY")
        print("-" * 60)
        
        try:
            result = search_jobs(query, location)    
        except Exception as e:
            return {
                "success": False,
                "message": f"job search failed: {e}"
            }
            
        if isinstance(result, list):
            jobs = result
            
        elif isinstance(result, dict):
            jobs = (
                result.get("data", {})
                .get("data", {})
                .get("jobs", [])
            )        
        
            if not jobs:
                jobs = (result.get("data", {})
                        .get("data", {})
                        .get("items", []))
            
        else:
            jobs = []
            
        if not jobs:
            return {
                "success": False,
                "message": (
                    f"No verified live jobs found for '{query}' in '{location}'.")
            }        
            
        print(f"[JARVIS] Found {len(jobs)} jobs.") 
        
        
        filtered_jobs = []

        for job in jobs:
            print(f"[DEBUG] Job location received: {job.get('location', '')}")
            if location_matches(job.get("location", ""), location):
                filtered_jobs.append(job)

        print(
                f"[JARVIS] {len(filtered_jobs)} jobs match "
                f"the required location."
            )

        jobs = filtered_jobs

        if not jobs:
            return {
                "success": False,
                "message": (
                f"No jobs found for '{query}' in '{location}'. "
                "Try another location."
            )
        }        
        
        print("\n" + "-" * 60)
        print("🔎 PHASE 3 — JOB ANALYSIS")
        print("-" * 60)
        print("✓ Reading job pages")
        print("✓ Extracting job requirements")
        
        analyzed_jobs = []
        
        for job in jobs:
            if not isinstance(job, dict):
                continue
            
            match = calculate_match(
                job,
                candidate_profile,
                query,
                location
            )
            
            analyzed_jobs.append(match)
            
        if not analyzed_jobs:
            return {
                "success": False,
                "message": "Jobs were found but could not be analyzed."
            }
            
        print("\n" + "-" * 60)
        print("🧩 PHASE 4 — CANDIDATE MATCHING")
        print("-" * 60)
        print("✓ Comparing resume with job requirements")
        print("✓ Calculating match scores")
        
        analyzed_jobs.sort(key=lambda job: job["score"], reverse=True)
        
        print("\n" + "-" * 60)
        print("🏆 PHASE 5 — RANKING & RECOMMENDATION")
        print("-" * 60)
        print("✓ Ranking opportunities")
        print("✓ Selecting the strongest match")
        
        top_jobs = analyzed_jobs[:10]
        
        if top_jobs:
            best_job = top_jobs[0]

            print("\n" + "-" * 60)
            print("🤖 JARVIS DECISION ENGINE")
            print("-" * 60)

            print(
                f"✓ Strongest opportunity: "
                f"{best_job.get('title', 'Unknown')}"
            )

            print(
                f"✓ Company: "
                f"{best_job.get('company', 'Unknown company')}"
            )

            print(
                f"✓ Match score: "
                f"{best_job.get('score', 0)}%"
            )

            print(
                f"✓ Confidence: "
                f"{best_job.get('confidence', 'low').upper()}"
            )

            print(
                f"✓ Recommendation: "
                f"{best_job.get('recommendation', 'REVIEW')}"
            )
        
        return {
            "success": True,
            "query": query,
            "location": location,
            "total_jobs": len(jobs),
            "jobs": top_jobs
        }    