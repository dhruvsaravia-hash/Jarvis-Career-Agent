import re

USER_SKILLS = {
    "python",
    "c",
    "c++",
    "java",
    "javascript",
    "html",
    "css",
    "data structures",
    "algorithms",
    "dsa",
    "object oriented programming",
    "oop",
    "git",
    "github",
    "problem solving",    
}

def normalize(text):
    if not text:
        return ""
    
    return text.lower()

def find_skills(text):
    """
    Find skills mentioned in a job description.
    """
    
    text = normalize(text)
    
    found = set()
    
    for skill in USER_SKILLS:
        pattern=re.escape(skill)
        
        if re.search(r"\b"+pattern+r"\b", text):
            found.add(skill)
            
    return found

def calculate_match(job):
    
    text = " ".join([str(job.get("title", "")),
                     str(job.get("company", "")),
                     str(job.get("snippet", "")),])
    
    job_skills = find_skills(text)
    
    matched = job_skills.intersection(USER_SKILLS)
    missing = job_skills - USER_SKILLS 
    
    if job_skills:
        score = round(len(matched)/len(job_skills) * 100)
    else:
        score = 0
        
    return {
        "title": job.get("title"),
        "company": job.get("company"),
        "location": job.get("location"),
        "salary": job.get("salary"),
        "url": job.get("url"),
        "score": score,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
    }
           