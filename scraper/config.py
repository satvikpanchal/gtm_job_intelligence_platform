"""
Main Scraper Configuration
All proxy info, API endpoints, and settings in one place.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# REDIS
# ============================================================================
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUE_NAME = "jobs"

# ============================================================================
# DIRECTORIES
# ============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "scraped")
REGISTRY_FILE = os.path.join(BASE_DIR, "data", "registry.json")

# ============================================================================
# REQUEST SETTINGS
# ============================================================================
REQUEST_TIMEOUT = 15
MAX_RETRIES = 5
BASE_BACKOFF = 1.5

# ============================================================================
# WORKER SETTINGS
# ============================================================================
DEFAULT_WORKERS = 50

# ============================================================================
# PROXY CONFIGURATION (Webshare)
# ============================================================================
def _parse_proxy_list():
    """Parse PROXY_LIST env var into list of dicts."""
    proxy_str = os.getenv("PROXY_LIST", "")
    if not proxy_str:
        return []
    proxies = []
    for entry in proxy_str.split(","):
        if ":" in entry:
            ip, port = entry.strip().split(":")
            proxies.append({"ip": ip, "port": port})
    return proxies

PROXIES = _parse_proxy_list()
PROXY_USER = os.getenv("PROXY_USER", "")
PROXY_PASS = os.getenv("PROXY_PASS", "")
USE_PROXIES = bool(PROXY_USER and PROXY_PASS and PROXIES)

# ============================================================================
# ATS API ENDPOINTS
# These APIs return job descriptions inline - no HTML scraping needed!
# ============================================================================
ATS_APIS = {
    "greenhouse": {
        "url": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
        "jobs_path": "jobs",
        "job_id": "id",
        "job_title": "title",
        "job_location": lambda j: j.get("location", {}).get("name", ""),
        "job_url": lambda slug, j: f"https://boards.greenhouse.io/{slug}/jobs/{j.get('id', '')}",
        "job_content": "content",  # HTML content
    },
    "lever": {
        "url": "https://api.lever.co/v0/postings/{slug}?mode=json",
        "jobs_path": None,  # Root is list
        "job_id": "id",
        "job_title": "text",
        "job_location": lambda j: j.get("categories", {}).get("location", ""),
        "job_url": lambda slug, j: j.get("hostedUrl", ""),
        "job_content": "descriptionPlain",  # Plain text
    },
    "ashby": {
        "url": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
        "jobs_path": "jobs",
        "job_id": "id",
        "job_title": "title",
        "job_location": lambda j: j.get("location", ""),
        "job_url": lambda slug, j: j.get("jobUrl", f"https://jobs.ashbyhq.com/{slug}/{j.get('id', '')}"),
        "job_content": "descriptionPlain",  # Plain text
    },
    "smartrecruiters": {
        "url": "https://api.smartrecruiters.com/v1/companies/{slug}/postings",
        "jobs_path": "content",
        "job_id": "id",
        "job_title": "name",
        "job_location": lambda j: j.get("location", {}).get("city", ""),
        "job_url": lambda slug, j: f"https://jobs.smartrecruiters.com/{slug}/{j.get('id', '')}",
        "job_content": None,  # Requires separate API call
    },
}

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
]
