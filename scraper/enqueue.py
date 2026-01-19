"""
Enqueue - Load companies and add to Redis queue.
Uses built-in companies list - no discovery needed!
"""

import argparse
from redis import Redis
from rq import Queue

from .config import REDIS_URL, QUEUE_NAME
from .companies import COMPANIES, TOTAL_COMPANIES, BY_ATS


def enqueue_all(limit: int = None) -> int:
    """
    Enqueue all companies to Redis queue.
    Returns count of jobs enqueued.
    """
    companies = COMPANIES[:limit] if limit else COMPANIES
    
    if not companies:
        return 0
    
    # Connect to Redis
    redis_conn = Redis.from_url(REDIS_URL)
    queue = Queue(QUEUE_NAME, connection=redis_conn)
    
    # Clear existing jobs
    queue.empty()
    
    print("=" * 60)
    print(f"📋 ENQUEUING {len(companies)} COMPANIES")
    print(f"   Queue: {QUEUE_NAME}")
    print(f"   Redis: {REDIS_URL}")
    print("   By ATS:", ", ".join(f"{k}: {v}" for k, v in BY_ATS.items()))
    print("=" * 60)
    
    count = 0
    for company in companies:
        ats = company.get("ats")
        slug = company.get("slug")
        name = company.get("name", slug)
        
        if not ats or not slug:
            continue
        
        queue.enqueue(
            "main_scraper.tasks.scrape_company_task",
            ats, slug, name,
            job_timeout=120,
            result_ttl=3600,
        )
        count += 1
    
    print(f"✅ Enqueued {count} companies")
    print(f"🚀 Start workers: python -m main_scraper.run 50")
    
    return count


def main():
    parser = argparse.ArgumentParser(description="Enqueue companies for scraping")
    parser.add_argument("--limit", type=int, help="Max companies to enqueue")
    args = parser.parse_args()
    
    enqueue_all(args.limit)


if __name__ == "__main__":
    main()
