import html
import re

SKILL_CATALOG = {
    "python": ("python",),
    "php": ("php",),
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
    "system design": ("system design", "system design basics"),
    "testing": ("testing", "software testing"),
    "debugging": ("debugging", "debug"),
    "agile": ("agile",),
    "documentation": ("documentation", "technical documentation"),
    "react": ("react", "react.js"),
    "angular": ("angular",),
    "next.js": ("next.js", "nextjs"),
    "node.js": ("node.js", "nodejs"),
    "aws": ("aws",),
    "machine learning": ("machine learning", "ml"),
    "artificial intelligence": ("artificial intelligence", "ai"),
    "docker": ("docker",),
    "linux": ("linux",),
    "express.js": ("express.js", "expressjs"),
    "mongodb": ("mongodb", "mongo db"),
    "typescript": ("typescript",),
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

def extract_required_skills(page_text):
    text = normalize(page_text)

    sections = [
        "skills you'll use",
        "technical skills",
        "requirements",
        "required skills",
        "who can apply",
        "qualifications",
        "what we're looking for",
    ]

    relevant_text = ""

    for section in sections:
        index = text.find(section)

        if index != -1:
            relevant_text += text[index:index + 1500] + " "

    return find_skills(relevant_text)
    
def location_matches(job_location, preferred_location):

    if isinstance(job_location, dict):
        job_location = job_location.get("raw", "")

    job_location = normalize(job_location)
    preferred_location = normalize(preferred_location)
    
    if not preferred_location:
        return True
    
    if "mumbai" in preferred_location:
        mumbai_area = [
            "mumbai",
            "thane",
            "navi mumbai",
            "ghansoli",
            "sanpada",
            "chembur",
            "vidyavihar",
            "bombay",
            "vasai",
            "virar",
            "bhayandar",
            "maharashtra",
        ]    
        
        return any(place in job_location for place in mumbai_area)
    
    if "pune" in preferred_location:
        pune_area=[
            "pune",
            "pimpri",
            "chinchwad",
            "maharashtra"
        ]
        
        return any(place in job_location for place in pune_area)
    
    return preferred_location in job_location   

def query_matches(job_text, query):
    ignored_words = {"internship", "intern", "job", "jobs", "role", "positions", "looking", "for"}
    
    terms = [
        term
        for term in re.findall(r"[a-zA-Z+#.]+", normalize(query))
        if term not in ignored_words
    ]     
    
    if not terms:
        return True
    
    matched_terms = sum(1 for term in terms if contains_term(job_text, term))
    return matched_terms >= max(1, len(terms) // 2)

def extract_required_skills(page_text):
    text = normalize(page_text)

    section_keywords = [
        "skills",
        "technical skills",
        "requirements",
        "required skills",
        "qualifications",
        "what we're looking for",
        "responsibilities",
        "job description",
    ]

    relevant_text = ""

    for section in section_keywords:
        index = text.find(section)

        if index != -1:
            relevant_text += text[index:index + 3000] + " "

    if not relevant_text.strip():
        relevant_text = text[:6000]
        
    return find_skills(relevant_text)

def calculate_match(job, candidate, query="", preferred_location=""):
    title=str(job.get("title",""))
    snippet=str(job.get("snippet",""))
    category =str(job.get("category",""))
    employment_type=str(job.get("employment_type",""))
    page_text=str(job.get("page_text", ""))
    core_job_text=normalize(title + " " + snippet + " " + category + " " + employment_type)
    
    job_text = normalize(core_job_text + " " + page_text)
    
    core_skills = find_skills(title)
    
    required_skills = extract_required_skills(page_text)
    if not required_skills:
        required_skills = find_skills(title + " " + snippet)

    job_skills = core_skills.union(required_skills)
    
    candidate_skills = set(candidate["skills"])
    
    matched = job_skills.intersection(candidate_skills)
    missing = job_skills - candidate_skills
    
    internship_text = normalize(title + " " + str(job.get("job_type", "")) + " " + str(job.get("employment_type", "")))
    
    if not job_skills:
        skill_score=30
    else:    
        skill_score = round(len(matched)/len(job_skills)*100)   
         
    location_score = 100 if location_matches(job.get("location", ""), preferred_location) else 40
    internship_score = 100 if "intern" in internship_text else 40
    education_score = 100 if candidate.get("education") else 50
    
    role_match = query_matches(job_text, query)
    query_text = normalize(query)
    
    wants_internship = ("intern" in query_text or "internship" in query_text)
    
    internship_text = normalize(title + " " + str(job.get("job_type", "")) + " " + str(job.get("employment_type", "")))
    
    is_internship = "intern" in internship_text
    
    if wants_internship:
        if is_internship:
            role_score = 100
            score_penalty = 0
        else:
            role_score = 0  
            score_penalty = 60
    else:
        role_score = 100 if role_match else 0
        score_penalty = 30 if not role_match else 0
                
    score = round(
                  skill_score*0.60
                  +role_score*0.15
                  +location_score*0.10
                  +internship_score*0.10
                  +education_score*0.05
                  -score_penalty
                  )
    
    if len(job_skills)<=1:
        score=min(score, 74)
        
    signals = (
        len(job_skills)
        +int(query_matches(job_text, query))
        +int("intern" in job_text)
    )    
    
    confidence = "high" if signals>=3 else "medium" if signals else "low"
    
    if len(job_skills) <= 3:
        score = min(score, 85)
        
    source_quality = job.get("source_quality", "unknown")

    if (
        score >= 80
        and len(matched) >= len(missing)
        and role_match
        and len(job_skills) >= 5
        and source_quality in ("verified", "unverified")
    ):
        recommendation = "APPLY"

    elif (
        score >= 70
        and role_match
        and source_quality == "verified"
    ):
        recommendation = "CONSIDER"

    elif score >= 55:
        recommendation = "CONSIDER"

    else:
        recommendation = "REVIEW"
        
    strengths = sorted(matched)
    strengths.append("hands-on-project")
    strengths.append(candidate["education"])
    
    source = job.get("source", "Unknown source")
    source_quality = job.get("source_quality", "unknown")

    return {
        "title": title or "Unknown title",
        "company": job.get("company") or "Unknown company",
        "location": job.get("location") or "Not specified",
        "salary": job.get("salary") or "Not specified",
        "url": job.get("url") or "",
        "source": source,
        "source_quality": source_quality,        
        "score": score,
        "confidence": confidence,
        "recommendation": recommendation,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "strengths": strengths,
    }    
    
def build_candidate_from_resume(resume_text):
    skills=find_skills(resume_text)
    return {
        "skills": skills,
        "education": "Education found in resume" if resume_text else "",
        "projects":[]
    }                