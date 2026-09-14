import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ANAKIN_API_KEY = os.getenv("ANAKIN_API_KEY")
BASE_URL = "https://api.anakin.io"


# ============================================================
# ANAKIN API
# ============================================================

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
            f"Task creation failed ({response.status_code}): "
            f"{response.text}"
        )

    job_id = response.json().get("job_id")

    if not job_id:
        raise RuntimeError(
            "Anakin did not return a job_id."
        )

    poll_url = f"{BASE_URL}/v1/wire/jobs/{job_id}"

    for attempt in range(30):

        response = requests.get(
            poll_url,
            headers=get_headers(),
            timeout=30
        )

        if not response.ok:
            raise RuntimeError(
                f"Polling failed ({response.status_code}): "
                f"{response.text}"
            )

        result = response.json()
        status = result.get("status")

        if status in ("completed", "succeeded"):
            return result

        if status in ("failed", "error"):
            raise RuntimeError(
                f"Anakin task failed: {result}"
            )

        retry_after = result.get(
            "retry_after_ms",
            2000
        )

        time.sleep(retry_after / 1000)

    raise RuntimeError(
        "Anakin task timed out after 30 polling attempts."
    )


# ============================================================
# RESULT EXTRACTION
# ============================================================

def extract_items(result):
    """
    Extract job items from the common Anakin response structure.
    """

    if not isinstance(result, dict):
        return []

    data = result.get("data", {})

    if not isinstance(data, dict):
        return []

    data = data.get("data", {})

    if not isinstance(data, dict):
        return []

    items = data.get("items", [])

    if isinstance(items, list):
        return items

    jobs = data.get("jobs", [])

    if isinstance(jobs, list):
        return jobs

    return []


# ============================================================
# AMAZON JOBS
# ============================================================

def normalize_amazon_jobs(jobs):

    normalized = []

    for job in jobs:

        if not isinstance(job, dict):
            continue

        company = job.get("company", "")

        if isinstance(company, dict):
            company = company.get("name", "")

        location = job.get("location", "")

        if isinstance(location, dict):
            location = location.get("raw", "")

        normalized.append({
            **job,
            "company": str(company or ""),
            "location": str(location or ""),
            "url": (
                job.get("application_url")
                or job.get("url")
                or ""
            ),
            "snippet": job.get("snippet", "")
        })

    return normalized


def search_amazon_jobs(query, location):

    queries = [query]

    words_to_remove = {
        "internship",
        "intern",
        "job",
        "jobs",
        "role",
        "positions"
    }

    cleaned_words = [
        word
        for word in query.split()
        if word.lower() not in words_to_remove
    ]

    cleaned_query = " ".join(cleaned_words).strip()

    if (
        cleaned_query
        and cleaned_query.lower() != query.lower()
    ):
        queries.append(cleaned_query)

    for current_query in queries:

        for start in range(0, 250, 50):

            params = {
                "query": current_query,
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

            jobs = normalize_amazon_jobs(
                extract_items(result)
            )

            if not jobs:
                break

            location_lower = location.lower()

            matching_jobs = []

            for job in jobs:

                job_location = str(
                    job.get("location", "")
                ).lower()

                if location_lower in job_location:
                    matching_jobs.append(job)

            if matching_jobs:

                internship_jobs = []

                for job in matching_jobs:

                    title = str(
                        job.get("title", "")
                    ).lower()

                    job_type = str(
                        job.get("job_type", "")
                    ).lower()

                    employment_type = str(
                        job.get("employment_type", "")
                    ).lower()

                    if (
                        "intern" in title
                        or "intern" in job_type
                        or "intern" in employment_type
                    ):
                        internship_jobs.append(job)

                if internship_jobs:
                    return internship_jobs

    return []


# ============================================================
# INDEED
# ============================================================

def search_indeed_jobs(query, location):

    params = {
        "query": query,
        "location": location,
        "start": 0,
        "sort": "relevance",
        "country_domain": "in"
    }

    result = run_anakin_action(
        "in_search_jobs",
        params
    )

    return extract_items(result)


# ============================================================
# MICROSOFT
# ============================================================

def search_microsoft_jobs(query, location):

    params = {
        "search_query": query,
        "location": location,
        "start": "0",
        "sort_by": "relevance",
        "filter_profession": "Software Engineering"
    }

    result = run_anakin_action(
        "act_apply_careers_microsoft_job_search_listing",
        params
    )

    return extract_items(result)


# ============================================================
# META
# ============================================================

def search_meta_jobs(query, location):

    params = {
        "search_query": query,
        "location": location,
    }

    result = run_anakin_action(
        "act_metacareers_job_search_listing",
        params
    )

    return extract_items(result)


# ============================================================
# COMPANY EXTRACTION
# ============================================================

def extract_company_from_title(title):

    title = str(title or "").strip()

    if not title:
        return ""

    # Remove endings such as "| Careers", "| Jobs", "| Internships"
    cleaned = re.sub(
        r"\s*\|\s*(careers?|jobs?|job openings?|internships?)$",
        "",
        title,
        flags=re.IGNORECASE
    ).strip()

    parts = [
        part.strip()
        for part in re.split(
            r"\s+-\s+|\s*\|\s*",
            cleaned
        )
        if part.strip()
    ]

    if not parts:
        return ""

    generic_words = {
        "career",
        "careers",
        "career page",
        "jobs",
        "job",
        "job openings",
        "job listing",
        "job listings",
        "intern",
        "internship",
        "internships",
        "developer",
        "developers",
        "engineer",
        "engineering",
        "software",
        "software developer",
        "software engineer",
        "python",
        "java",
        "javascript",
        "ai",
        "machine learning",
        "data",
        "technology",
        "technologies",
        "company",
        "employment",
        "opportunities",
        "apply now",
        "job board"
    }

    job_words = [
        "intern",
        "internship",
        "developer",
        "engineer",
        "software",
        "python",
        "java",
        "javascript",
        "machine learning",
        "data analyst",
        "data science",
        "data analytics",
        "frontend",
        "backend",
        "full stack",
        "apply now",
        "job board"
    ]

    def is_job_or_generic(part):
        part_lower = part.lower().strip()

        if part_lower in generic_words:
            return True

        return any(
            re.search(
                rf"\b{re.escape(word)}\b",
                part_lower
            )
            for word in job_words
        )

    def is_location(part):
        part_lower = part.lower().strip()

        location_patterns = [
            r"^[a-z .'-]+,\s*[a-z .'-]+$",
            r"^(remote|hybrid|work from home)$",
            r"^(mumbai|pune|thane|delhi|bangalore|bengaluru|hyderabad)$"
        ]

        return any(
            re.search(
                pattern,
                part_lower,
                re.IGNORECASE
            )
            for pattern in location_patterns
        )

    # FIX: Extract employer from Unstop-style titles
    # Example:
    # "Software Engineer Intern - Google - Unstop"
    # -> Google
    unstop_match = re.search(
        r"\b(?:developer intern|software engineer intern|internship|intern)"
        r"\s*[-–|]\s*(.+?)"
        r"\s*[-–|]\s*unstop$",
        cleaned,
        re.IGNORECASE
    )

    if unstop_match:
        company = unstop_match.group(1).strip()

        if (
            company
            and not is_job_or_generic(company)
            and not is_location(company)
        ):
            return company

    # Example:
    # "Software Developer at Microsoft"
    # -> Microsoft
    at_match = re.search(
        r"\bat\s+(.+?)(?=\s+\||\s+-\s+|\s+–\s+|$)",
        cleaned,
        re.IGNORECASE
    )

    if at_match:
        company = at_match.group(1).strip()

        if (
            company
            and not is_job_or_generic(company)
            and not is_location(company)
        ):
            return company

    # Example:
    # "Hiring Google - Software Engineer"
    # -> Google
    hiring_match = re.search(
        r"\bhiring\s+(.+?)(?=\s*:\s*|\s+\||\s+-\s+|\s+–\s+|$)",
        cleaned,
        re.IGNORECASE
    )

    if hiring_match:
        company = hiring_match.group(1).strip()

        if (
            company
            and not is_job_or_generic(company)
            and not is_location(company)
        ):
            return company

    # Example:
    # "Software Engineer from Microsoft"
    # -> Microsoft
    from_match = re.search(
        r"\bfrom\s+(.+?)(?=\s+\||\s+-\s+|\s+–\s+|$)",
        cleaned,
        re.IGNORECASE
    )

    if from_match:
        company = from_match.group(1).strip()

        if (
            company
            and not is_job_or_generic(company)
            and not is_location(company)
        ):
            return company

    # General fallback:
    # Check parts from right to left and use the first
    # part that does not look like a job title or location.
    for part in reversed(parts):

        if is_job_or_generic(part):
            continue

        if is_location(part):
            continue

        return part

    return ""
def read_job_page(url):

    if not url:
        return ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0 Safari/537.36"
        )
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        return response.text

    except requests.exceptions.RequestException:
        return ""


# ============================================================
# TAVILY WEB SEARCH
# ============================================================

def search_web_jobs(query, location):

    tavily_key = os.getenv("TAVILY_API_KEY")

    if not tavily_key:
        print(
            "[JARVIS] TAVILY_API_KEY is missing."
        )
        return []

    search_query = (
        f'"{query}" "{location}" '
        f'("intern" OR "internship" OR "job") '
        f'("apply" OR "application" OR "careers") '
        f'-youtube -instagram -reddit '
        f'-blog -article -guide -tutorial '
        f'-visa -salary -negotiation'
    )

    print(
        f"[JARVIS] Web search query: "
        f"{search_query}"
    )

    try:

        response = requests.post(
            "https://api.tavily.com/search",
            headers={
                "Authorization":
                    f"Bearer {tavily_key}",
                "Content-Type":
                    "application/json"
            },
            json={
                "query": search_query,
                "search_depth": "advanced",
                "max_results": 20,
                "include_answer": False,
                "include_raw_content": True
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        print(
            f"[JARVIS] Tavily returned "
            f"{len(results)} results."
        )

        jobs = []

        trusted_domains = {
            "linkedin.com",
            "indeed.com",
            "unstop.com",
            "wellfound.com",
            "builtin.com",
            "adzuna.in",
            "keka.com",
            "freshershunt.in",
            "hiretoday.in",
            "wizzer.in",
            "fresherscareer.in",
            "atlss.in"
        }

        job_words = [
            "intern",
            "internship",
            "developer",
            "software engineer",
            "software development",
            "data analyst",
            "data analytics",
            "data science",
            "career",
            "job opening",
            "job openings",
            "hiring",
            "vacancy",
            "apply"
        ]
        
        blocked_domains = {
            "wikipedia.org",
            "britannica.com",
            "incredibleindia.gov.in",
            "mumbaitourism.travel",
            "oecd.org"
        }

        blocked_url_words = [
            "/jobs?",
            "/jobs/",
            "/internships?",
            "/internship/",
            "/search",
            "/search?",
            "/collections/",
            "/category/",
            "/categories/"
        ]
        for result in results:

            title = (
                result.get("title") or ""
            ).strip()

            url = (
                result.get("url") or ""
            ).strip()

            content = (
                result.get("content") or ""
            ).strip()

            raw_content = (
                result.get("raw_content") or ""
            ).strip()

            if not title or not url:
                continue
            
            url_lower = url.lower()

            if any(
                domain in url_lower
                for domain in blocked_domains
            ):
                print(
                    f"[DEBUG] Rejected blocked domain: {title}"
                )
                continue

            if any(
                blocked_word in url_lower
                for blocked_word in blocked_url_words
            ):
                print(
                    f"[DEBUG] Rejected listing/search page: {title}"
                )
                continue

            combined_text = (
                title + " "
                + content + " "
                + raw_content
            )                        
            if any(blocked_word in url.lower() for blocked_word in blocked_url_words):
                print(f"[DEBUG] Rejected listing/search page: {title}")
                continue
            
            if any(domain in url.lower() for domain in blocked_domains):
                print(f"[DEBUG] Rejected blocked domain: {title}")
                continue

            if any(blocked_word in url.lower() for blocked_word in blocked_url_words):
                print(f"[DEBUG] Rejected listing/search page: {title}")
                continue
            
            combined_text = (title + " " + content + " " + raw_content)

            job_text = combined_text.lower()
            title_lower = title.lower()
            url_lower = url.lower()
            
            # --------------------------------------------------------
            # REJECT NON-JOB / DISCUSSION PAGES
            # --------------------------------------------------------

            blocked_page_patterns = [
                "groups.google.com",
                "reddit.com",
                "youtube.com",
                "wikipedia.org",
                "/blog/",
                "/article/",
                "/news/",
                "/forum/",
                "/discussion/",
            ]

            if any(pattern in url_lower for pattern in blocked_page_patterns):
                print(f"[DEBUG] Rejected non-job page: {title}")
                continue

            
            # --------------------------------------------------------
            # REJECT OBVIOUSLY OLD JOB RESULTS
            # --------------------------------------------------------

            current_year = 2026

            old_year_match = re.search(
                r"\b(20\d{2})\b",
                title
            )

            if old_year_match:
                result_year = int(old_year_match.group(1))

                if result_year < current_year:
                    print(
                        f"[DEBUG] Rejected old job result "
                        f"({result_year}): {title}"
                    )
                    continue
            if any(domain in url_lower for domain in blocked_domains):
                print(f"[DEBUG] Rejected blocked domain: {title}")
                continue
            print(
                f"[DEBUG] Checking result: {title}"
            )
            print(
                f"[DEBUG] URL: {url}"
            )
            print(
                f"[DEBUG] Contains location? "
                f"{location.lower() in job_text}"
            )

            # ------------------------------------------------
            # JOB FILTER
            # ------------------------------------------------

            query_lower = query.lower()

            title_has_job_word = any(
                re.search(
                    rf"\b{re.escape(word)}\b",
                    title_lower
                )
                for word in job_words
            )

            if "internship" in query_lower or "intern" in query_lower:
                title_is_relevant = (
                    re.search(r"\bintern(ship)?\b", title_lower)
                    or re.search(r"\btrainee\b", title_lower)
                )
            else:
                title_is_relevant = title_has_job_word

            if not title_is_relevant:
                print(
                    f"[DEBUG] Rejected by title relevance filter: "
                    f"{title}"
                )
                continue

            # ------------------------------------------------
            # LOCATION FILTER
            # ------------------------------------------------

                        # ------------------------------------------------
            # QUERY-SPECIFIC ROLE FILTER
            # ------------------------------------------------

            query_words = [
                word
                for word in re.findall(
                    r"\b[a-zA-Z][a-zA-Z+#.-]*\b",
                    query_lower
                )
                if word not in {
                    "intern",
                    "internship",
                    "job",
                    "jobs",
                    "role",
                    "opening",
                    "opportunity"
                }
            ]

            role_keywords_found = 0

            for word in query_words:
                if re.search(
                    rf"\b{re.escape(word)}\b",
                    job_text
                ):
                    role_keywords_found += 1

            if query_words and role_keywords_found == 0:
                print(
                    f"[DEBUG] Rejected: query role not found: "
                    f"{title}"
                )
                continue
            

            if location.lower() not in job_text:
                continue

            # ------------------------------------------------
            # COMPANY EXTRACTION
            # ------------------------------------------------

            company = ""

            known_companies = [
                "google",
                "microsoft",
                "amazon",
                "meta",
                "apple",
                "ibm",
                "accenture",
                "tcs",
                "infosys",
                "wipro",
                "capgemini",
                "cognizant",
                "deloitte",
                "pwc",
                "ey",
                "kpmg",
                "oracle",
                "adobe",
                "nvidia",
                "intel",
                "salesforce"
            ]

            for known_company in known_companies:

                if known_company in title_lower:
                    company = known_company.title()
                    break

            if not company:
                company = extract_company_from_title(title)
                
                # Fallback: extract company from the job URL
                if not company and url:
                    domain_match = re.search(
                        r"https?://(?:www\.)?([^./]+)\.",
                        url,
                        re.IGNORECASE
                    )

                    if domain_match:
                        domain_company = domain_match.group(1).strip()

                        blocked_domains = {
                            "linkedin",
                            "indeed",
                            "naukri",
                            "unstop",
                            "glassdoor",
                            "internshala",
                            "foundit",
                            "wellfound",
                            "adzuna",
                            "candidhr",
                            "workday",
                            "google",
                            "microsoft",
                            "amazon"
                        }

                        if domain_company.lower() not in blocked_domains:
                            company = (
                                domain_company
                                .replace("-", " ")
                                .replace("_", " ")
                                .title()
                            )
                        
                        if company.lower() == "edwards":
                            company = "Edwards Lifesciences"

                        if company.lower() == "reliancegames":
                            company = "Reliance Games"    
    
                platform_names = {
                        "unstop",
                        "jobleads",
                        "linkedin",
                        "indeed",
                        "glassdoor",
                        "naukri",
                        "internshala",
                        "foundit",
                        "wellfound",
                        "adzuna"
                    }        

            if company.lower().strip() in platform_names:
                company = ""
                        
            # ------------------------------------------------
            # KEKA COMPANY EXTRACTION
            # ------------------------------------------------

            if not company and "keka.com" in url_lower:

                keka_match = re.search(
                    r"https?://([^.]+)\.keka\.com",
                    url,
                    re.IGNORECASE
                )

                if keka_match:

                    company = (
                        keka_match.group(1)
                        .replace("-", " ")
                        .replace("_", " ")
                        .title()
                    )

            # ------------------------------------------------
            # JSON-LD COMPANY EXTRACTION
            # ------------------------------------------------

            if not company and raw_content:

                company_match = re.search(
                    r'"hiringOrganization"\s*:\s*'
                    r'\{.*?"name"\s*:\s*"([^"]+)"',
                    raw_content,
                    re.IGNORECASE | re.DOTALL
                )

                if company_match:
                    company = (
                        company_match.group(1)
                        .strip()
                    )

            # ------------------------------------------------
            # CLEAN COMPANY NAME
            # ------------------------------------------------

            if company:

                company = re.sub(
                    r"\s*\|\s*(careers?|jobs?|internships?)$",
                    "",
                    company,
                    flags=re.IGNORECASE
                ).strip()

            invalid_company_names = {
                "",
                "career",
                "careers",
                "jobs",
                "job",
                "intern",
                "internship",
                "internships",
                "developer",
                "software developer",
                "software engineer",
                "unknown"
            }

            if company.lower() in invalid_company_names:
                company = ""

            # ------------------------------------------------
            # SOURCE QUALITY
            # ------------------------------------------------

            source_quality = "unverified"

            if any(
                domain in url_lower
                for domain in trusted_domains
            ):
                source_quality = "verified"

            # ------------------------------------------------
            # CREATE JOB
            # ------------------------------------------------
            actual_location = ""

            location_patterns = [
                r"\b(remote|work from home|wfh)\b",
                r"\b(mumbai|navi mumbai|thane|pune|pimpri|chinchwad)\b",
                r"\b(bangalore|bengaluru|hyderabad|delhi|noida|gurgaon|gurugram)\b",
                r"\b(chennai|kolkata|ahmedabad|jaipur|indore)\b",
            ]

            for pattern in location_patterns:
                location_match = re.search(
                    pattern,
                    combined_text,
                    re.IGNORECASE
                )

                if location_match:
                    actual_location = location_match.group(1).strip()
                    break

            if not actual_location:
                actual_location = "Unknown"

            print(
                f"[DEBUG] Actual job location detected: "
                f"{actual_location}"
            )


            job_data = {
                "title": title,
                "company": company,
                "location": actual_location,
                "url": url,
                "snippet": content,
                "page_text": (
                    raw_content
                    or content
                ),
                "employment_type": (
                    "Internship"
                    if "intern" in job_text
                    else ""
                ),
                "source": "Web Search",
                "source_quality": source_quality
            }

            jobs.append(job_data)

            print(
                f"[JARVIS] Web job found: "
                f"{title} | "
                f"{company or 'Unknown company'}"
            )

        print(
            f"[JARVIS] ✓ {len(jobs)} "
            f"live web jobs collected"
        )

        return jobs

    except requests.exceptions.RequestException as e:

        print(
            f"[JARVIS] Web search request failed: {e}"
        )

        return []

    except Exception as e:

        print(
            f"[JARVIS] Web search processing failed: {e}"
        )

        return []


# ============================================================
# MAIN JOB SEARCH
# ============================================================

def search_jobs(query, location):

    sources = [
        ("Amazon Jobs", search_amazon_jobs),
        ("Indeed", search_indeed_jobs),
        ("Microsoft Careers", search_microsoft_jobs),
        ("Meta Careers", search_meta_jobs),
        ("Web Search", search_web_jobs)
    ]

    all_jobs = []

    for source_name, source_function in sources:

        print(
            f"→ {source_name:<20}",
            end=""
        )

        try:

            jobs = source_function(
                query,
                location
            )

            if not jobs:

                print(
                    f" [JARVIS DEBUG] "
                    f"{source_name} returned 0 jobs"
                )

                continue

            print(
                f" [JARVIS DEBUG] "
                f"{source_name} returned "
                f"{len(jobs)} jobs"
            )

            for job in jobs:

                if not isinstance(job, dict):
                    continue

                url = (
                    job.get("url")
                    or job.get("application_url")
                    or ""
                )

                title = str(
                    job.get("title", "")
                ).strip()

                # --------------------------------------------
                # COMPANY FROM TITLE
                # --------------------------------------------

                if (
                    not job.get("company")
                    and title
                ):

                    job["company"] = (
                        extract_company_from_title(
                            title
                        )
                    )

                # --------------------------------------------
                # READ JOB PAGE
                # --------------------------------------------

                if url:

                    page_text = read_job_page(
                        url
                    )

                    if page_text:

                        job["page_text"] = (
                            page_text
                        )

                    # ----------------------------------------
                    # COMPANY FROM PAGE
                    # ----------------------------------------

                    if (
                        not job.get("company")
                        and page_text
                    ):

                        company_match = re.search(
                            r'"hiringOrganization"\s*:\s*'
                            r'\{.*?"name"\s*:\s*"([^"]+)"',
                            page_text,
                            re.IGNORECASE | re.DOTALL
                        )

                        if company_match:

                            job["company"] = (
                                company_match
                                .group(1)
                                .strip()
                            )

                    # ----------------------------------------
                    # COMPANY FROM KEKA URL
                    # ----------------------------------------

                    if not job.get("company"):

                        keka_match = re.search(
                            r"https?://([^.]+)\.keka\.com",
                            url,
                            re.IGNORECASE
                        )

                        if keka_match:

                            job["company"] = (
                                keka_match.group(1)
                                .replace("-", " ")
                                .replace("_", " ")
                                .title()
                            )

                # --------------------------------------------
                # FINAL COMPANY CLEANUP
                # --------------------------------------------

                if job.get("company"):

                    job["company"] = re.sub(
                        r"\s*\|\s*(careers?|jobs?|internships?)$",
                        "",
                        str(job["company"]),
                        flags=re.IGNORECASE
                    ).strip()

                all_jobs.append(job)

        except Exception as e:

            error_text = str(e).lower()

            print(
                f"\n[JARVIS DEBUG] "
                f"{source_name} failed:"
            )

            print(
                f"[JARVIS DEBUG] {e}"
            )

            if (
                "insufficient_credits"
                in error_text
                or "402"
                in error_text
            ):

                print(
                    "⚠ Credits unavailable"
                )

            elif (
                "auth_expired"
                in error_text
                or "authentication"
                in error_text
            ):

                print(
                    "⚠ Authentication unavailable"
                )

            else:

                print(
                    "⚠ Source unavailable"
                )

            continue

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    if all_jobs:

        unique_jobs = []
        seen_urls = set()

        for job in all_jobs:

            url = (
                job.get("url")
                or job.get("application_url")
                or ""
            )

            if url:

                if url in seen_urls:
                    continue

                seen_urls.add(url)

            unique_jobs.append(job)

        return unique_jobs

    return []