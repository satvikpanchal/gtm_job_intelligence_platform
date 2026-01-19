"""Enqueue companies for LLM extraction - BATCH STRATEGY (10 jobs per task)."""

import os
import json
from pathlib import Path
from redis import Redis
from rq import Queue
from .config import REDIS_URL, EXTRACT_QUEUE
from .tasks import BATCH_SIZE, DEFAULT_RETRY

# Redis connection
redis_conn = Redis.from_url(REDIS_URL)
queue = Queue(EXTRACT_QUEUE, connection=redis_conn)

# Data directory
SCRAPED_DIR = Path(__file__).parent.parent / "data" / "scraped"


def get_scraped_companies():
    """Get all scraped companies with their jobs."""
    companies = []
    
    for ats_dir in SCRAPED_DIR.iterdir():
        if not ats_dir.is_dir():
            continue
        
        ats = ats_dir.name
        
        for json_file in ats_dir.glob("*.json"):
            company = json_file.stem
            
            with open(json_file) as f:
                data = json.load(f)
            
            jobs = data.get("jobs", [])
            if jobs:
                companies.append({
                    "ats": ats,
                    "company": company,
                    "jobs": jobs
                })
    
    return companies


def chunk_jobs(jobs: list, batch_size: int = BATCH_SIZE):
    """Split jobs into batches of batch_size."""
    for i in range(0, len(jobs), batch_size):
        yield i // batch_size, jobs[i:i + batch_size]


def enqueue_all(limit: int = None, company_limit: int = None):
    """
    Enqueue all companies for extraction using BATCH STRATEGY.
    
    Each company's jobs are split into batches of 10.
    This gives much better parallelism than 1 task per company.
    
    Args:
        limit: Limit total number of batches (for testing)
        company_limit: Limit number of companies
    """
    from .tasks import extract_job_batch
    
    companies = get_scraped_companies()
    
    if company_limit:
        companies = companies[:company_limit]
    
    total_batches = 0
    total_jobs = 0
    
    print(f"📋 Enqueueing {len(companies)} companies with batch strategy (max {BATCH_SIZE} jobs/task)...")
    print("=" * 60)
    
    for c in companies:
        jobs = c["jobs"]
        num_batches = (len(jobs) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_id, batch in chunk_jobs(jobs):
            if limit and total_batches >= limit:
                print(f"\n⚠️  Reached batch limit of {limit}")
                break
                
            queue.enqueue(
                extract_job_batch,
                ats=c["ats"],
                company=c["company"],
                batch_id=batch_id,
                jobs=batch,
                job_timeout="10m",  # Shorter timeout for smaller batches
                retry=DEFAULT_RETRY  # Retry 3x with backoff
            )
            total_batches += 1
            total_jobs += len(batch)
        
        if limit and total_batches >= limit:
            break
            
        print(f"  ✓ {c['ats']}/{c['company']}: {len(jobs)} jobs → {num_batches} batches")
    
    print("=" * 60)
    print(f"\n✅ Enqueued {total_batches} batches ({total_jobs} jobs)")
    print(f"📊 Queue length: {len(queue)}")
    print(f"⚡ With 3 workers, ~{total_batches // 3} batches each")


def enqueue_all_legacy(limit: int = None):
    """Legacy: Enqueue 1 task per company (not recommended)."""
    from .tasks import extract_company_jobs
    
    companies = get_scraped_companies()
    
    if limit:
        companies = companies[:limit]
    
    print(f"⚠️  Using legacy enqueue (1 task per company)")
    
    for c in companies:
        queue.enqueue(
            extract_company_jobs,
            ats=c["ats"],
            company=c["company"],
            jobs=c["jobs"],
            job_timeout="30m"
        )
        print(f"  ✓ {c['ats']}/{c['company']} ({len(c['jobs'])} jobs)")
    
    print(f"\n✅ Enqueued {len(companies)} companies")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Enqueue extraction jobs")
    parser.add_argument("--limit", type=int, help="Limit number of batches")
    parser.add_argument("--company-limit", type=int, help="Limit number of companies")
    parser.add_argument("--legacy", action="store_true", help="Use legacy 1-task-per-company")
    args = parser.parse_args()
    
    if args.legacy:
        enqueue_all_legacy(limit=args.limit)
    else:
        enqueue_all(limit=args.limit, company_limit=args.company_limit)


if __name__ == "__main__":
    main()
    main()
