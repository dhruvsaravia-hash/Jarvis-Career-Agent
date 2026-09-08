import html
import re

SKILL_CATALOG = {
    "python": ("python",),
    "c": ("c",),
    "c++": ("c++", "cpp"),
    "java": ("java",),
    "javascript": ("javascript", "js"),
    "html": ("html",),
    "css": ("css",),
    "data structures": ("data structures", "dsa"),
    "algorithms": ("algorithms",),
    "oop": ("object oriented programming", "oop"),
    "git": ("git", "github"),
    "django": ("django",),
    "flask": ("flask",),
    "fastapi": ("fastapi",),
    "sql": ("sql", "mysql", "postgresql"),
    "rest api": ("rest api", "restful"),
    "react": ("react", "react.js"),
    "angular": ("angular",),
    "next.js": ("next.js", "nextjs"),
    "node.js": ("node.js", "nodejs"),
    "aws": ("aws",),
    "machine learning": ("machine learning", "ml"),
    "artificial intelligence": ("artificial intelligence", "ai"),
    "docker": ("docker",),
    "linux": ("linux",),
}

def normalize(text):
    text = html.unescape(str(text or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()

def contains_term(text, term):
    pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
    return re.search(pattern, text) is not None
    
def find_skills(text):
    text = normalize(text)
    found = set()    
    
    for skill, aliases in SKILL_CATALOG.items():
        for alias in aliases:
            if contains_term(text, alias):
                found.add(skill)
                break
    return found
    
def location_matches(job_location, preferred_location):
    job_location = normalize(job_location)
    preferred_location = normalize(preferred_location)
    
    if "mumbai" in preferred_location:
        mumbai_area = [
             "mumbai",
            "thane",
            "navi mumbai",
            "ghansoli",
            "sanpada",
            "chembur",
            "vidyavihar",
            "maharashtra",
        ]    
        
        return any(place in job_location for place in mumbai_area)

    return preferred_location in job_location   

def query_matches(job_text, query):
    ignored_words = {"internship", "intern", "job", "jobs"}
    
    terms = [
        term
        for term in re.findall(r"[a-zA-Z+#.]+", normalize(query))
        if term not in ignored_words
    ]     
    
    return any(contains_term(job_text, term) for term in terms)

def calculate_match(job, candidate, query="", preferred_location=""):
    title=str(job.get("title",""))
    snippet=str(job.get("snippet",""))
    job_text=normalize(title + " " + snippet)
    
    job_skills = find_skills(job_text)
    candidate_skills = set(candidate["skills"])
    
    matched = job_skills.intersection(candidate_skills)
    missing = job_skills - candidate_skills
    
    skill_score = 50 if not job_skills else round(len(matched)/len(job_skills)*100)
    role_score = 100 if query_matches(job_text, query) else 35  
    location_score = 100 if location_matches(job.get("location", ""), preferred_location) else 40
    internship_score = 100 if ("intern" in job_text or "intern" in normalize(job.get("job_type",""))) else 40
    education_score = 100 if candidate.get("education") else 50
    
    score = round(
        skill_score*0.55
                  +role_score*0.15
                  +location_score*0.10
                  +internship_score*0.10
                  +education_score*0.10
                  )
    
    if len(job_skills)<=1:
        score=min(score, 74)
        
    signals = (
        len(job_skills)
        +int(query_matches(job_text, query))
        +int("intern" in job_text)
    )    
    
    confidence = "high" if signals>=3 else "medium" if signals else "low"
    
    if len(job_skills) <= 1:
        confidence = "medium"
        
    if score >= 75 and len(matched)>=len(missing):
        recommendation = "APPLY"
    elif score >= 55:
        recommendation = "CONSIDER"
    else:
        recommendation = "REVIEW"
        
    strengths = sorted(matched)
    strengths.append("hands-on-project")
    strengths.append(candidate["education"])
    
    return {
        "title": title or "Unknown title",
        "company": job.get("company") or "Unknown company",
        "location": job.get("location") or "Not specified",
        "salary": job.get("salary") or "Not specified",
        "url": job.get("url") or "",
        "score": score,
        "confidence": confidence,
        "recommendation": recommendation,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "strengths": strengths,
    }                