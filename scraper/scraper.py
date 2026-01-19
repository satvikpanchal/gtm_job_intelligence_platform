"""
Core Scraper - Extracts job descriptions directly from ATS APIs.
No HTML scraping needed - APIs return descriptions inline!
"""

import requests
import json
import os
import random
import time
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from bs4 import BeautifulSoup

from .config import (
    PROXIES, PROXY_USER, PROXY_PASS, USE_PROXIES,
    ATS_APIS, USER_AGENTS, OUTPUT_DIR,
    REQUEST_TIMEOUT, MAX_RETRIES, BASE_BACKOFF
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_proxy() -> Optional[dict]:
    """Get a random proxy with authentication."""
    if not USE_PROXIES or not PROXIES:
        return None
    proxy = random.choice(PROXIES)
    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{proxy['ip']}:{proxy['port']}"
    return {"http": proxy_url, "https": proxy_url}


def make_request(url: str, retries: int = MAX_RETRIES) -> Optional[dict]:
    """
    Make HTTP request with proxy rotation and retry logic.
    Returns parsed JSON or None on failure.
    """
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/html",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                headers=headers,
                proxies=get_proxy(),
                timeout=REQUEST_TIMEOUT
            )
            
            if resp.status_code == 200:
                return resp.json()
            
            # Retryable status codes
            if resp.status_code in (429, 500, 502, 503, 504):
                delay = BASE_BACKOFF ** attempt + random.random()
                logger.warning(f"Status {resp.status_code}, retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            
            # Non-retryable failure
            logger.error(f"Request failed with status {resp.status_code}: {url}")
            return None
            
        except Exception as e:
            delay = BASE_BACKOFF ** attempt + random.random()
            logger.warning(f"Request error (attempt {attempt}): {e}")
            time.sleep(delay)
    
    logger.error(f"Request failed after {retries} attempts: {url}")
    return None


def clean_html(html: str) -> str:
    """Convert HTML to clean plain text."""
    if not html:
        return ""
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script/style
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        
        # Get text with line breaks
        text = soup.get_text(separator='\n')
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    except:
        # Fallback: basic HTML tag removal
        return re.sub(r'<[^>]+>', ' ', html).strip()


def fetch_smartrecruiters_description(slug: str, job_id: str) -> str:
    """
    Fetch job description from SmartRecruiters posting API.
    SmartRecruiters doesn't include description in the list API - need to fetch each job.
    """
    if not job_id:
        return ""
    
    # SmartRecruiters job detail endpoint
    detail_url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{job_id}"
    data = make_request(detail_url)
    
    if not data:
        logger.warning(f"Failed to fetch SmartRecruiters job detail: {slug}/{job_id}")
        return ""
    
    # The job description is in the 'jobAd' field with 'sections'
    job_ad = data.get("jobAd", {})
    sections = job_ad.get("sections", {})
    
    # Collect all section content
    description_parts = []
    
    # Standard sections: jobDescription, qualifications, additionalInformation
    for section_key in ["jobDescription", "qualifications", "additionalInformation", "companyDescription"]:
        section = sections.get(section_key, {})
        if section:
            title = section.get("title", "")
            text = section.get("text", "")
            if text:
                if title:
                    description_parts.append(f"## {title}")
                # Clean HTML from text
                clean_text = clean_html(text)
                description_parts.append(clean_text)
    
    return "\n\n".join(description_parts)


def scrape_company(ats: str, slug: str, company_name: str) -> Dict[str, Any]:
    """
    Scrape all jobs from a company.
    Returns dict with company info and list of jobs with descriptions.
    """
    logger.info(f"Scraping {company_name} ({ats}/{slug})")
    
    # Get ATS config
    ats_config = ATS_APIS.get(ats)
    if not ats_config:
        return {"error": f"Unknown ATS: {ats}", "company": company_name}
    
    # Make API request
    api_url = ats_config["url"].format(slug=slug)
    data = make_request(api_url)
    
    if data is None:
        return {"error": "API request failed", "company": company_name}
    
    # Extract jobs list
    jobs_path = ats_config.get("jobs_path")
    if jobs_path:
        raw_jobs = data.get(jobs_path, [])
    else:
        raw_jobs = data if isinstance(data, list) else []
    
    # Parse each job
    jobs = []
    for job in raw_jobs:
        # Get location (can be string or lambda)
        location_getter = ats_config["job_location"]
        location = location_getter(job) if callable(location_getter) else job.get(location_getter, "")
        
        # Get URL
        url_getter = ats_config["job_url"]
        url = url_getter(slug, job) if callable(url_getter) else job.get(url_getter, "")
        
        # Get content/description
        content_key = ats_config.get("job_content")
        if content_key:
            raw_content = job.get(content_key, "")
            # Clean HTML if it looks like HTML
            if raw_content and ('<' in raw_content or '&lt;' in raw_content):
                # Unescape HTML entities first
                import html
                raw_content = html.unescape(raw_content)
                content = clean_html(raw_content)
            else:
                content = raw_content
        elif ats == "smartrecruiters":
            # SmartRecruiters requires a separate API call per job
            content = fetch_smartrecruiters_description(slug, job.get("id", ""))
        else:
            content = ""
        
        jobs.append({
            "id": str(job.get(ats_config["job_id"], "")),
            "title": job.get(ats_config["job_title"], ""),
            "location": location,
            "url": url,
            "description": content,
        })
    
    logger.info(f"✅ {company_name}: {len(jobs)} jobs")
    
    return {
        "company": company_name,
        "slug": slug,
        "ats": ats,
        "jobs_count": len(jobs),
        "jobs": jobs,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def save_company_jobs(result: Dict[str, Any]) -> str:
    """Save scraped jobs to final_jobs_scraped directory."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    slug = result.get("slug", "unknown")
    ats = result.get("ats", "unknown")
    
    # Create subdirectory for ATS
    ats_dir = os.path.join(OUTPUT_DIR, ats)
    os.makedirs(ats_dir, exist_ok=True)
    
    # Save JSON
    output_path = os.path.join(ats_dir, f"{slug}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    return output_path


def scrape_and_save(ats: str, slug: str, company_name: str) -> Dict[str, Any]:
    """
    Main task: Scrape a company and save results.
    This is the function called by RQ workers.
    """
    result = scrape_company(ats, slug, company_name)
    
    if "error" not in result:
        path = save_company_jobs(result)
        result["saved_to"] = path
        
        # Count jobs with descriptions
        jobs_with_desc = sum(1 for j in result.get("jobs", []) if j.get("description"))
        result["jobs_with_description"] = jobs_with_desc
        logger.info(f"💾 Saved to {path} ({jobs_with_desc}/{result['jobs_count']} with descriptions)")
    
    return result
