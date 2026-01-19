"""
RQ Tasks - Worker task definitions for Redis Queue.
"""

from .scraper import scrape_and_save


def scrape_company_task(ats: str, slug: str, company_name: str) -> dict:
    """
    RQ Task: Scrape a company and save jobs to final_jobs_scraped.
    
    This function is enqueued to Redis and executed by workers.
    Each worker picks up a company, scrapes all jobs with descriptions,
    and saves to final_jobs_scraped/{ats}/{slug}.json
    """
    return scrape_and_save(ats, slug, company_name)
