import os
import re
import time
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

ANAKIN_API_KEY = os.getenv("ANAKIN_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

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
        raise RuntimeError("Anakin did not return a job_id.")

    poll_url = f"{BASE_URL}/v1/wire/jobs/{job_id}"

    for _ in range(30):

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
        "Anakin task timed out."
    )


# ============================================================
# RESULT EXTRACTION
# ============================================================

def extract_items(result):

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
# AMAZON
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

    params = {
        "query": query,
        "start": 0,
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

    return [
        job for job in jobs
        if location.lower() in str(
            job.get("location", "")
        ).lower()
    ]


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
        "location": location
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

    # Common formats:
    #
    # Software Engineer Intern - Google
    # Data Analyst Intern | Deloitte
    # Software Developer at Microsoft
    # Google - Software Engineer Intern

    patterns = [

        r"\bat\s+(.+?)(?:\s*\||\s+-\s+|$)",

        r"^(.+?)\s+-\s+"
        r"(?:software|data|python|web|backend|frontend|"
        r"full.?stack|machine learning|ai|developer|engineer|"
        r"analyst)",

        r"^(.+?)\s*\|\s*"
        r"(?:software|data|python|web|backend|frontend|"
        r"full.?stack|machine learning|ai|developer|engineer|"
        r"analyst)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            title,
            re.IGNORECASE
        )

        if match:

            company = match.group(1).strip()

            if company:
                return company

    # Known companies

    known_companies = [
        "Google",
        "Microsoft",
        "Amazon",
        "Meta",
        "Apple",
        "IBM",
        "Accenture",
        "TCS",
        "Infosys",
        "Wipro",
        "Capgemini",
        "Cognizant",
        "Deloitte",
        "PwC",
        "EY",
        "KPMG",
        "Oracle",
        "Adobe",
        "NVIDIA",
        "Intel",
        "Salesforce"
    ]

    title_lower = title.lower()

    for company in known_companies:

        if company.lower() in title_lower:
            return company

    return ""


# ============================================================
# JOB PAGE
# ============================================================

def read_job_page(url):

    if not url:
        return ""

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/140.0 Safari/537.36"
                )
            },
            timeout=12
        )

        if response.ok:
            return response.text

    except requests.RequestException:
        pass

    return ""


# ============================================================
# TAVILY WEB SEARCH
# ============================================================

def search_web_jobs(query, location):

    if not TAVILY_API_KEY:

        print(
            "[JARVIS] TAVILY_API_KEY is missing."
        )

        return []

    # Multiple searches give Tavily a better chance of finding
    # individual job pages instead of listing pages.

    queries = [

        f'"{query}" "{location}" internship apply',

        f'"{query}" "{location}" intern careers',

        f'"{query}" "{location}" "apply now"',

    ]

    all_results = []

    try:

        for search_query in queries:

            print(
                f"[JARVIS] Web search query: "
                f"{search_query}"
            )

            response = requests.post(
                "https://api.tavily.com/search",
                headers={
                    "Authorization":
                        f"Bearer {TAVILY_API_KEY}",
                    "Content-Type":
                        "application/json"
                },
                json={
                    "query": search_query,
                    "search_depth": "advanced",
                    "max_results": 10,
                    "include_answer": False,
                    "include_raw_content": True
                },
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            results = data.get(
                "results",
                []
            )

            all_results.extend(results)

        print(
            f"[JARVIS] Tavily returned "
            f"{len(all_results)} total results."
        )

    except requests.RequestException as e:

        print(
            f"[JARVIS] Tavily search failed: {e}"
        )

        return []

    jobs = []
    seen_urls = set()

    # Platforms that commonly contain individual jobs
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
        "atlss.in",
        "internshala.com",
        "glassdoor.co.in",
        "naukri.com"
    }

    blocked_domains = {
        "youtube.com",
        "reddit.com",
        "wikipedia.org",
        "facebook.com",
        "instagram.com"
    }

    listing_phrases = [
        "jobs in",
        "job vacancies",
        "job vacancy",
        "jobs near",
        "all jobs",
        "job listings",
        "job listing",
        "internships in",
        "internship vacancies",
        "search jobs",
        "find jobs",
        "job search"
    ]

    for result in all_results:

        if not isinstance(result, dict):
            continue

        title = str(
            result.get("title", "")
        ).strip()

        url = str(
            result.get("url", "")
        ).strip()

        content = str(
            result.get("content", "")
        ).strip()

        raw_content = str(
            result.get("raw_content", "")
        ).strip()

        if not title or not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)

        title_lower = title.lower()
        url_lower = url.lower()

        # ----------------------------------------------------
        # BLOCK BAD DOMAINS
        # ----------------------------------------------------

        if any(
            domain in url_lower
            for domain in blocked_domains
        ):
            continue

        # ----------------------------------------------------
        # BLOCK LISTING PAGES
        # ----------------------------------------------------

        if any(
            phrase in title_lower
            for phrase in listing_phrases
        ):
            print(
                f"[DEBUG] Rejected listing page: "
                f"{title}"
            )
            continue

        # ----------------------------------------------------
        # JOB RELEVANCE
        # ----------------------------------------------------

        job_text = (
            title + " " +
            content + " " +
            raw_content
        ).lower()

        internship_search = (
            "intern" in query.lower()
            or "internship" in query.lower()
        )

        if internship_search:

            if not re.search(
                r"\bintern(ship)?\b|\btrainee\b",
                title_lower
            ):

                print(
                    f"[DEBUG] Rejected non-internship: "
                    f"{title}"
                )

                continue

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        location_lower = location.lower()

        location_aliases = {
            "mumbai": [
                "mumbai",
                "bombay",
                "navi mumbai",
                "thane",
                "bhiwandi"
            ],

            "pune": [
                "pune",
                "pimpri",
                "chinchwad"
            ]
        }

        aliases = location_aliases.get(
            location_lower,
            [location_lower]
        )

        if not any(
            alias in job_text
            for alias in aliases
        ):

            print(
                f"[DEBUG] Rejected wrong location: "
                f"{title}"
            )

            continue

        # ----------------------------------------------------
        # QUERY RELEVANCE
        # ----------------------------------------------------

        query_terms = re.findall(
            r"[a-zA-Z]+",
            query.lower()
        )

        ignored = {
            "intern",
            "internship",
            "job",
            "jobs",
            "role",
            "opening",
            "opportunity"
        }

        query_terms = [
            word
            for word in query_terms
            if word not in ignored
        ]

        if query_terms:

            matches = sum(
                1
                for word in query_terms
                if re.search(
                    rf"\b{re.escape(word)}\b",
                    job_text
                )
            )

            # At least one meaningful query term
            if matches == 0:

                print(
                    f"[DEBUG] Rejected unrelated role: "
                    f"{title}"
                )

                continue

        # ----------------------------------------------------
        # COMPANY
        # ----------------------------------------------------

        company = extract_company_from_title(
            title
        )

        # Known company from title

        known_companies = [
            "Google",
            "Microsoft",
            "Amazon",
            "Meta",
            "Apple",
            "IBM",
            "Accenture",
            "TCS",
            "Infosys",
            "Wipro",
            "Capgemini",
            "Cognizant",
            "Deloitte",
            "PwC",
            "EY",
            "KPMG",
            "Oracle",
            "Adobe",
            "NVIDIA",
            "Intel",
            "Salesforce"
        ]

        for known in known_companies:

            if known.lower() in title_lower:

                company = known
                break

        # ----------------------------------------------------
        # COMPANY FROM DOMAIN
        # ----------------------------------------------------

        if not company:

            try:

                hostname = urlparse(url).hostname or ""

                parts = hostname.split(".")

                if len(parts) >= 2:

                    domain_company = parts[-2]

                    blocked_company_domains = {
                        "linkedin",
                        "indeed",
                        "naukri",
                        "unstop",
                        "glassdoor",
                        "internshala",
                        "wellfound",
                        "adzuna",
                        "freshershunt"
                    }

                    if (
                        domain_company.lower()
                        not in blocked_company_domains
                    ):

                        company = (
                            domain_company
                            .replace("-", " ")
                            .title()
                        )

            except Exception:
                pass

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        actual_location = location

        # Remote should not be mislabeled as Mumbai
        if re.search(
            r"\bremote\b|\bwork from home\b|\bwfh\b",
            title_lower
        ):

            actual_location = "Remote"

        else:

            for alias in aliases:

                if alias in job_text:

                    actual_location = alias.title()
                    break

        # ----------------------------------------------------
        # CREATE JOB
        # ----------------------------------------------------

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
                if re.search(
                    r"\bintern(ship)?\b",
                    job_text
                )
                else ""
            ),

            "source": "Web Search",

            "source_quality": (
                "verified"
                if any(
                    domain in url_lower
                    for domain in trusted_domains
                )
                else "unverified"
            )
        }

        jobs.append(job_data)

        print(
            f"[JARVIS] ✓ Web job found: "
            f"{title} | "
            f"{company or 'Unknown company'} | "
            f"{actual_location}"
        )

        # We only need a handful for the demo.
        if len(jobs) >= 10:
            break

    print(
        f"[JARVIS] ✓ "
        f"{len(jobs)} live web jobs collected"
    )

    return jobs


# ============================================================
# MAIN JOB SEARCH
# ============================================================

def search_jobs(query, location):

    sources = [

        (
            "Amazon Jobs",
            search_amazon_jobs
        ),

        (
            "Indeed",
            search_indeed_jobs
        ),

        (
            "Microsoft Careers",
            search_microsoft_jobs
        ),

        (
            "Meta Careers",
            search_meta_jobs
        )

    ]

    all_jobs = []

    # --------------------------------------------------------
    # ANAKIN SOURCES
    # --------------------------------------------------------

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

            print(
                f" [JARVIS DEBUG] "
                f"{source_name} returned "
                f"{len(jobs)} jobs"
            )

            for job in jobs:

                if not isinstance(job, dict):
                    continue

                if not job.get("url"):
                    job["url"] = (
                        job.get("application_url")
                        or ""
                    )

                if not job.get("company"):

                    job["company"] = (
                        extract_company_from_title(
                            job.get(
                                "title",
                                ""
                            )
                        )
                    )

                job.setdefault(
                    "source",
                    source_name
                )

                job.setdefault(
                    "source_quality",
                    "verified"
                )

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

            else:

                print(
                    "⚠ Source unavailable"
                )

    # --------------------------------------------------------
    # TAVILY FALLBACK
    # --------------------------------------------------------

    print(
        "\n→ Web Search"
    )

    web_jobs = search_web_jobs(
        query,
        location
    )

    all_jobs.extend(web_jobs)

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    unique_jobs = []

    seen_urls = set()

    for job in all_jobs:

        url = str(
            job.get("url", "")
        ).strip()

        if url:

            if url in seen_urls:
                continue

            seen_urls.add(url)

        unique_jobs.append(job)

    print(
        f"[JARVIS] Total unique jobs: "
        f"{len(unique_jobs)}"
    )

    return unique_jobs