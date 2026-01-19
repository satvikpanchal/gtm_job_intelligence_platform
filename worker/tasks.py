"""RQ tasks for distributed job processing - BATCH STRATEGY."""

import json
import os
import fcntl
from redis import Redis
from rq import Queue, Retry
from .config import REDIS_URL, SCRAPE_QUEUE, EXTRACT_QUEUE, EXTRACTED_DIR
from .extractor import extract_job, batch_extract

# Redis connection
redis_conn = Redis.from_url(REDIS_URL)
scrape_queue = Queue(SCRAPE_QUEUE, connection=redis_conn)
extract_queue = Queue(EXTRACT_QUEUE, connection=redis_conn)

# Batch size for extraction
BATCH_SIZE = 10

# Retry config: 3 attempts with exponential backoff (10s, 30s, 60s)
DEFAULT_RETRY = Retry(max=3, interval=[10, 30, 60])


def extract_job_batch(ats: str, company: str, batch_id: int, jobs: list) -> dict:
    """
    Extract structured data from a batch of jobs (max 10).
    
    Uses atomic file operations to append results to company file.
    Multiple batches can run in parallel for the same company.
    
    Args:
        ats: ATS platform (greenhouse, lever, etc.)
        company: Company slug
        batch_id: Batch number for this chunk
        jobs: List of raw job dictionaries (max 10)
        
    Returns:
        Summary of extraction results
    """
    print(f"🔍 Batch {batch_id}: Extracting {len(jobs)} jobs for {company} ({ats})")
    
    extracted_jobs = []
    errors = 0
    
    for job in jobs:
        result = extract_job(job)
        if "error" in result:
            errors += 1
        extracted_jobs.append(result)
    
    # Write batch results atomically
    output_dir = os.path.join(EXTRACTED_DIR, ats)
    os.makedirs(output_dir, exist_ok=True)
    
    # Write to batch file (simple, no locking needed)
    batch_file = os.path.join(output_dir, f"{company}_batch_{batch_id}.json")
    with open(batch_file, "w") as f:
        json.dump({
            "company": company,
            "ats": ats,
            "batch_id": batch_id,
            "jobs": extracted_jobs,
            "extracted": len(extracted_jobs) - errors,
            "errors": errors
        }, f, indent=2)
    
    print(f"✅ {company} batch {batch_id}: {len(extracted_jobs) - errors}/{len(jobs)} extracted")
    
    return {
        "company": company,
        "ats": ats,
        "batch_id": batch_id,
        "total": len(jobs),
        "extracted": len(extracted_jobs) - errors,
        "errors": errors
    }


def aggregate_company_batches(ats: str, company: str) -> dict:
    """
    Aggregate all batch files for a company into a single file.
    Call this after all batches are complete.
    """
    import glob
    
    batch_dir = os.path.join(EXTRACTED_DIR, ats)
    batch_pattern = os.path.join(batch_dir, f"{company}_batch_*.json")
    batch_files = sorted(glob.glob(batch_pattern))
    
    all_jobs = []
    total_extracted = 0
    total_errors = 0
    
    for batch_file in batch_files:
        with open(batch_file) as f:
            batch_data = json.load(f)
        all_jobs.extend(batch_data.get("jobs", []))
        total_extracted += batch_data.get("extracted", 0)
        total_errors += batch_data.get("errors", 0)
    
    # Write aggregated file
    output_file = os.path.join(batch_dir, f"{company}.json")
    with open(output_file, "w") as f:
        json.dump({
            "company": company,
            "ats": ats,
            "total_jobs": len(all_jobs),
            "extracted": total_extracted,
            "errors": total_errors,
            "jobs": all_jobs
        }, f, indent=2)
    
    # Clean up batch files
    for batch_file in batch_files:
        os.remove(batch_file)
    
    print(f"📦 Aggregated {len(batch_files)} batches for {company}: {len(all_jobs)} jobs")
    
    return {
        "company": company,
        "ats": ats,
        "total_jobs": len(all_jobs),
        "extracted": total_extracted,
        "errors": total_errors
    }


# Keep legacy function for compatibility
def extract_company_jobs(ats: str, company: str, jobs: list) -> dict:
    """Legacy: Extract all jobs for a company (use extract_job_batch instead)."""
    print(f"⚠️  Using legacy extract_company_jobs - consider using batch strategy")
    
    extracted_jobs = []
    errors = 0
    
    for job in jobs:
        result = extract_job(job)
        if "error" in result:
            errors += 1
        extracted_jobs.append(result)
    
    output_dir = os.path.join(EXTRACTED_DIR, ats)
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"{company}.json")
    with open(output_file, "w") as f:
        json.dump({
            "company": company,
            "ats": ats,
            "total_jobs": len(jobs),
            "extracted": len(extracted_jobs) - errors,
            "errors": errors,
            "jobs": extracted_jobs
        }, f, indent=2)
    
    return {
        "company": company,
        "ats": ats,
        "total": len(jobs),
        "extracted": len(extracted_jobs) - errors,
        "errors": errors
    }


def enqueue_extraction(ats: str, company: str, jobs: list):
    """Enqueue a company's jobs for extraction (legacy)."""
    extract_queue.enqueue(
        extract_company_jobs,
        ats=ats,
        company=company,
        jobs=jobs,
        job_timeout="30m"
    )
