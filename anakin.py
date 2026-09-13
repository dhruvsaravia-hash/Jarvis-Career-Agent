import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ANAKIN_API_KEY = os.getenv("ANAKIN_API_KEY")
BASE_URL = "https://api.anakin.io"


def get_headers():
    if not ANAKIN_API_KEY:
        raise RuntimeError(
            "ANAKIN_API_KEY is missing. Check your .env file."
        )

    return {
        "X-API-Key": ANAKIN_API_KEY,
        "Content-Type": "application/json",
    }


def run_anakin_action(action_id, params):
    """
    Run any Anakin Wire action and wait for the result.
    """

    payload = {
        "action_id": action_id,
        "params": params
    }

    response = requests.post(
        f"{BASE_URL}/v1/wire/task",
        headers=get_headers(),
        json=payload,
        timeout=30
    )

    if response.status_code != 202:
        raise RuntimeError(
            f"Task creation failed "
            f"({response.status_code}): {response.text}"
        )

    job_id = response.json().get("job_id")

    if not job_id:
        raise RuntimeError("Anakin did not return a job_id.")

    poll_url = f"{BASE_URL}/v1/wire/jobs/{job_id}"

    for attempt in range(30):

        response = requests.get(
            poll_url,
            headers=get_headers(),
            timeout=30
        )

        if not response.ok:
            raise RuntimeError(f"Polling failed ({response.status_code}): {response.text}")

        result = response.json()
        status = result.get("status")

        if status in ("completed", "succeeded"):
            return result

        if status in ("failed", "error"):
            raise RuntimeError(f"Anakin task failed: {result}")

        retry_after = result.get("retry_after_ms", 2000)

        time.sleep(retry_after / 1000)

    raise RuntimeError("Anakin task timed out after 30 polling attempts.")


def extract_items(result):
    """
    Extract job items from an Anakin search result.
    """

    try:
        return (
            result
            .get("data", {})
            .get("data", {})
            .get("items", [])
        )
    except AttributeError:
        return []


def normalize_amazon_jobs(jobs):
    normalized = []
    
    for job in jobs:
        company = job.get("company", "")
        if isinstance(company, dict):
            company = company.get("name", "")
            
        location = job.get("location", "")
        if isinstance(location, dict):
            location = location.get("raw", "")
                
        normalized.append({
            **job,
            "company": company,
            "location": location,
            "url": job.get("application_url") or job.get("url") or "",
            "snippet": job.get("snippet", "")
        })
    return normalized   

def read_job_page(url):
    """
    Fetch the public job page and return its text.
    """
    
    if not url:
        return ""
    
    headers={
        "User-Agent":(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0 Safari/537.36"
        )
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return ""
    
def search_amazon_jobs(query, location):
    """
    Search Amazon Jobs with pagination until jobs
    matching the requested location are found.
    """

    queries = [query]
    
    words_to_remove = {"internship", "intern", "job", "jobs", "role", "positions", "positions"}
    
    cleaned_words = [
        word for word in query.split()
        if word.lower() not in words_to_remove
    ]
    
    cleaned_query = " ".join(cleaned_words).strip()
    
    if cleaned_query and cleaned_query.lower() != query.lower():
        queries.append(cleaned_query)
    
    for current_query in queries:
        
        all_jobs = []

        for start in range(0, 250, 50):

            params = {
                "query": query,
                "start": start,
                "size": 50,
                "filter_facets": [],
                "location_facets": [],
                "sort": {
                    "sortType": "SCORE",
                    "sortOrder": "DESCENDING"
                }
            }

            result = run_anakin_action(
                "act_amazon_jobs_job_search_listing",
                params
            )

            jobs = extract_items(result)
            jobs = normalize_amazon_jobs(jobs)
            
            if not jobs:
                break
            
            all_jobs.extend(jobs)
            location_lower = location.lower()
            
            matching_jobs = []
            
            for job in jobs:

                job_location = job.get("location", "")

                if isinstance(job_location, dict):
                    job_location = job_location.get("raw", "")

                if location_lower in str(job_location).lower():
                    matching_jobs.append(job)

            if matching_jobs:
                internship_jobs = []

                for job in matching_jobs:
                    title = str(job.get("title", "")).lower()
                    job_type = str(job.get("job_type", "")).lower()
                    employment_type = str(job.get("employment_type", "")).lower()

                    if ("intern" in title or "intern" in job_type or "intern" in employment_type):
                        internship_jobs.append(job)

                if internship_jobs:
                    return internship_jobs

    return []

def search_indeed_jobs(query, location):
    
    params = {
        "query": query,
        "location": location,
        "start": 0,
        "sort": "relevance",
        "country_domain": "in" 
    }
    
    result = run_anakin_action("in_search_jobs", params)
    jobs = extract_items(result)
    
    return jobs

def search_microsoft_jobs(query, location):
    
    params = {
        "search_query": query,
        "location": location,
        "start": "0",
        "sort_by": "relevance",
        "filter_profession": "Software Engineering"
    }
    
    result = run_anakin_action("act_apply_careers_microsoft_job_search_listing", params)
    
    jobs = extract_items(result)
    
    return jobs

def search_meta_jobs(query, location):
    
    params = {
        "search_query": query,
        "location": location,
    }
    
    result = run_anakin_action("act_metacareers_job_search_listing", params)
    
    jobs = extract_items(result)
    
    return jobs

def search_web_jobs(query, location):
    
    tavily_key=os.getenv("TAVILY_API_KEY")
    
    if not tavily_key:
        print("[JARVIS] TAVILY_API_KEY is missing.")
        return []
    
    search_query = (
                    f'{query}" "{location} '
                    f'("software development intern" OR "software engineer intern" '
                    f'OR "Software developer intern" OR "developer intern") '
                    f'("apply" OR "application" OR "careers") '
                    f'-youtube -instagram -reddit -blog -article -guide -tutorial -tutorial'    
                    )
    try: 
        response = requests.post("https://api.tavily.com/search",
                                 headers={
                                     "Authorization": f"Bearer {tavily_key}",
                                     "Content-Type": "application/json"
                                 },
                                 json={
                                     "query": search_query,
                                     "search_depth": "advanced",
                                     "max_result": 20,
                                     "include_answer": False,
                                     "include_raw_content": True
                                 },
                                 timeout=30
                            )
        response.raise_for_status()
        data = response.json()
        results=data.get("results", [])
        
        jobs = []
        
        for result in results:
            title=(result.get("title") or "").strip()
            url=(result.get("url") or "").strip()
            content=(result.get("content") or "").strip()
            raw_content=(result.get("raw_content") or "").strip()
            
            combined_text = (title + " " + content + " " + raw_content)
            
            job_text = combined_text.lower()
            
            generic_page_words = [
                                  "jobs in", 
                                  "job search", 
                                  "job openings", 
                                  "search jobs", 
                                  "job listings", 
                                  "jobs page", 
                                  "career opportunities", 
                                  "internships in", 
                                  "internship listings",
                                  "job vacancies",
                                  "vacancies",
                                  "job vacancies in",
                                  "software developer intern jobs",
                                  "software internship jobs",
                                  "software intern jobs",
                                  "internship software jobs",
                                  "job vacancies",
                                  "jobs in mumbai",
                                  "jobs in india",
                                  "emploi(s) pour",
                                  ]
            blocked_url_terms = [
                "youtube.com",
                "youtu.be",
                "/blog/",
                "/article/",
                "/articles/",
                "/guide/",
                "/guides/",
                "/tutorial/",
                "/news/",
                "/programs/",
                "/program/",
                "linkedin.com/pulse/",
                "linkedin.com/posts/",
                "linkedin.com/feed/",            
            ]
            
            blocked_title_terms = [
                "how to",
                "what is",
                "thoughts on",
                "minimum every",
                "four-year internship program",
                "career center",
                "guide",
                "tutorial",
                "article",
            ]
            
            if any(term in title.lower() for term in blocked_title_terms):
                continue
            
            if any(term in url.lower() for term in blocked_url_terms):
                continue
            
            if re.match(r"intern\d+\s+.*internships?$", title, re.IGNORECASE):
                continue
            
            if "internshala.com/internships/" in url.lower():
                continue
            
            if re.search(r"\bjobs?\s*-\s*(naukri|indeed|linkedin|unstop)\b", title, re.IGNORECASE):
                continue
            
            non_job_titles = [
            "emploi(s) pour",
            "choice for",
            "discussion",
            "reddit",
            "pdf",
            "job search",
            "job listings",
            "internship listings",
            ]
                        
            if any(phrase in title.lower() for phrase in non_job_titles):
                continue
            
            listing_domains = [
                "glassdoor.",
                "naukri.com",
                "indeed.com",
                "linkedin.com/jobs",
                "foundit.in/search",
                "simplyhired.co.in",
                "shine.com",
                "instahyre.com",
            ]

            generic_url_terms = [
                "/internships",
                "/jobs",
                "/job-listings",
                "/internship-listings",
                "/career-opportunities",
                "indeed.co.in/",
                "indeed.com/",
            ]

            if any(term in url.lower() for term in generic_url_terms):
                continue
            
            if any(domain in url.lower() for domain in listing_domains):
                continue  
                  
            job_words = ["intern", "internship", "job", "developer", "software engineer", "software development", "job", "career"]
            
            if not any(word in job_text for word in job_words):
                continue
            
            company = ""

            title_lower = title.lower()
            url_lower = url.lower()
            job_text_lower = job_text.lower()

            known_companies = {
                "google": "Google",
                "microsoft": "Microsoft",
                "amazon": "Amazon",
                "meta": "Meta",
                "atlassian": "Atlassian",
                "apple": "Apple",
                "ibm": "IBM",
                "oracle": "Oracle",
                "accenture": "Accenture",
                "tcs": "TCS",
                "infosys": "Infosys",
                "wipro": "Wipro",
                "deloitte": "Deloitte",
                "capgemini": "Capgemini",
                "browserstack": "BrowserStack",
                "dg7": "DG7 Solutions",
                "adengage": "AdEngage",
                "aryaxai": "AryaXAI",
                "beam innovate": "Beam Innovate Pvt Ltd",
                "ventura securities": "Ventura Securities Ltd",
                "convergence it services": "Convergence IT Services",
            }

            for name, company_name in known_companies.items():
                if name in title_lower:
                    company = company_name
                    break

            if not company and "stackbinary" in title_lower:
                company = "Stackbinary"

            if not company and "stackbinary.io" in url_lower:
                company = "Stackbinary"

            if not company and "dg7" in title_lower:
                company = "DG7 Solutions"

            if not company and "dg7.in" in url_lower:
                company = "DG7 Solutions"

            if not company:
                parts = [p.strip() for p in re.split(r"\s+-\s+", title)]

                if len(parts) >= 2:
                    first_part = parts[0].lower()
                    second_part = parts[1].strip()

                    job_keywords = [
                        "intern",
                        "internship",
                        "developer",
                        "engineer",
                        "software",
                        "python",
                        "ai",
                        "machine learning",
                    ]

                    if any(word in first_part for word in job_keywords):
                        company = second_part

            if company:
                company = re.sub(
                    r"\s*\|\s*(Stackbinary Careers|Careers|Jobs|Internships?)$",
                    "",
                    company,
                    flags=re.IGNORECASE
                ).strip()

            if company.lower() in [
                "internships",
                "internship",
                "jobs",
                "job",
                "careers",
                "career",
                "company",
                "employer",
                "unknown",
                "n/a",
                "na",
                "adzuna.in",
            ]:
                company = ""

            if not company and ".keka.com/careers/" in url_lower:
                keka_match = re.search(
                    r"https?://([^.]+)\.keka\.com",
                    url,
                    re.IGNORECASE
                )

                if keka_match:
                    company = (
                        keka_match.group(1)
                        .replace("-", " ")
                        .title()
                    )

            if not company and "fresherscareer.in" in url_lower:
                company = "Freshers Career"

            if not company and "credenceanalytics.com" in url_lower:
                company = "Credence Analytics"

            if not company:
                bebee_match = re.search(
                    r"^(.+?)\s+-\s+(.+?)\s*\|\s*BeBee$",
                    title,
                    re.IGNORECASE
                )

                if bebee_match:
                    company = bebee_match.group(2).strip()

            if not company:
                snatcho_match = re.search(
                    r"Snatcho hiring .+?\s+in\s+",
                    title,
                    re.IGNORECASE
                )

                if snatcho_match:
                    company = "Snatcho"

            company = company.strip()

            if company.lower() in [
                "company",
                "employer",
                "unknown",
                "n/a",
                "na",
                "adzuna.in",
                "internships",
                "internship",
                "jobs",
                "careers",
            ]:
                company = ""
                                    
            source_quality = "unknown"

            trusted_domains = [
                "/careers/",
                "/career/",
                "/jobs/",
                "/job/",
                "linkedin.com",
                "indeed.com",
                "unstop.com",
                "wellfound.com",
                "builtin.com",
                "bebee.com",
                "keka.com",
                "freshershunt.in",
                "hiretoday.in",
                "credenceanalytics.com",
                "adzuna.in",
                "wizzer.in",
                "fresherscareer.in",
                "atlss.in",
            ]

            url_lower = url.lower()

            if any(domain in url_lower for domain in trusted_domains):
                source_quality = "verified"

            detected_location = location


            if location.lower() in combined_text.lower():
                detected_location = location
                job_data = {
                "title": title,
                "company": company,
                "location": detected_location,
                "url": url,
                "snippet": content,
                "page_text": raw_content or content,
                "employment_type": "Internship"
                if "intern" in job_text
                else "",
                "source": "Web Search",
                "source_quality": source_quality,
            }
            
            if source_quality == "unknown":
                source_quality = "unverified"
                print(f"⚠ Unverified source skipped: {url}")
            
            job_data["source_quality"] = source_quality
            jobs.append(job_data)        
                
        print(f"✓ {len(jobs)} live jobs collected")
            
        return jobs
    except requests.exceptions.RequestException as e:
        print(f"[JARVIS] Web search results failed: {e}")
        return []

def search_jobs(query, location):
    """
    Main job search function.

    Tries multiple job sources.
    If one fails, automatically moves to the next.
    """

    sources = [
        ("Amazon Jobs",search_amazon_jobs),
        ("Indeed",search_indeed_jobs),
        ("Microsoft Careers",search_microsoft_jobs),
        ("Meta Careers",search_meta_jobs),        
        ("Web Search", search_web_jobs)
    ]

    all_jobs = []
    for source_name, source_function in sources:

        print(f"→ {source_name:<20}", end="")

        try:
            jobs = source_function(query, location)

            if not jobs:
                continue

            matching_jobs = jobs

            if matching_jobs:
                
                for job in matching_jobs:
                    url = job.get("url") or job.get("application_url")

                    if url:
                        page_text = read_job_page(url)

                        job["page_text"] = page_text
                        
                        if not job.get("company") and page_text:
                            company_match = re.search(r'"hiringOrganization".*?"name"\s*:\s*"([^"]+)"', page_text, re.IGNORECASE)

                            if company_match:
                                job["company"] = company_match.group(1).strip()
                            
                all_jobs.extend(matching_jobs)
                continue

            print(
                f"[JARVIS] {source_name} returned jobs, "
                f"but none matched {location}."
            )

        except Exception as e:
            error_text = str(e).lower()

            if "insufficient_credits" in error_text or "402" in error_text:
                print("⚠ Credits unavailable")
            elif "auth_expired" in error_text or "authentication" in error_text:
                print("⚠ Authentication unavailable")
            else:
                print("⚠ Source unavailable")
            continue

    if all_jobs:
        unique_jobs = []
        seen_urls = set()
        
        for job in all_jobs:
            url = job.get("url") or job.get("application_url")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            unique_jobs.append(job)
        return unique_jobs        
            
    return []

def get_demo_jobs(query, location):

    return [
        {
            "title": "Python Developer Intern",
            "company": "TechNova Solutions",
            "location": "Mumbai, Maharashtra",
            "salary": "₹15,000/month",
            "snippet": (
                "Python Developer Intern. "
                "Skills: Python, Git, SQL, HTML, CSS. "
                "Internship for computer engineering students."
            ),
            "job_type": "Internship",
            "url": "DEMO-OFFLINE-JOB-1"
        },
        {
            "title": "Software Development Intern",
            "company": "Maitri Technologies",
            "location": "Navi Mumbai, Maharashtra",
            "salary": "₹12,000/month",
            "snippet": (
                "Software Development Internship. "
                "Skills: Python, C++, Data Structures, Algorithms, Git. "
                "Suitable for computer engineering students."
            ),
            "job_type": "Internship",
            "url": "DEMO-OFFLINE-JOB-2"
        },
        {
            "title": "Web Development Intern",
            "company": "DigitalWorks",
            "location": "Mumbai, Maharashtra",
            "salary": "₹10,000/month",
            "snippet": (
                "Web Development Intern. "
                "Skills: HTML, CSS, JavaScript, React, Git. "
                "Students can apply."
            ),
            "job_type": "Internship",
            "url": "DEMO-OFFLINE-JOB-3"
        },
        {
            "title": "Backend Developer Intern",
            "company": "CloudStack Technologies",
            "location": "Thane, Maharashtra",
            "salary": "₹14,000/month",
            "snippet": (
                "Backend Developer Intern. "
                "Skills: Python, Flask, SQL, REST API, Git. "
                "Computer engineering students preferred."
            ),
            "job_type": "Internship",
            "url": "DEMO-OFFLINE-JOB-4"
        },
        {
            "title": "Java Developer Intern",
            "company": "CodeSphere",
            "location": "Pune, Maharashtra",
            "salary": "₹12,000/month",
            "snippet": (
                "Java Developer Internship. "
                "Skills: Java, OOP, SQL, Git. "
                "Software engineering students."
            ),
            "job_type": "Internship",
            "url": "DEMO-OFFLINE-JOB-5"
        }
    ] 
    
def discover_web_actions():
    print("[JARVIS] Searching for web-reading actions...")

    queries = [
        "read webpage",
        "extract webpage content",
        "web page content",
        "scrape webpage"
    ]
    seen = set()    

    for query in queries:
        print(f"\n[JARVIS] Searching: {query}")

        response = requests.get(
            f"{BASE_URL}/v1/wire/search",
            headers=get_headers(),
            params={"query": query},
            timeout=30
        )

        if response.status_code != 200:
            print("ERROR:", response.text)
            continue

        results = response.json().get("results", [])

        for action in results:
            action_id = action.get("action_id")

            if not action_id or action_id in seen:
                continue

            seen.add(action_id)

            name = action.get("name", "")
            description = action.get("description", "")

            print("\n--------------------------------")
            print("ACTION ID:", action_id)
            print("NAME:", name)
            print("DESCRIPTION:", description)
            print("PARAMS:", action.get("params"))
    
    print("\n[JARVIS] Total unique actions:", len(seen))
if __name__ == "__main__":
    discover_web_actions()           