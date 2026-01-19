#!/usr/bin/env python3
"""
Quick Start Script - Run everything in one command.
Usage: python -m main_scraper.start [--limit N] [--workers N]
"""

import argparse
import subprocess
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="Scrape all companies with job descriptions")
    parser.add_argument("--limit", type=int, default=50, help="Max companies to scrape (default: 50)")
    parser.add_argument("--workers", type=int, default=50, help="Number of parallel workers (default: 50)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 MAIN SCRAPER - QUICK START")
    print(f"   Companies: {args.limit}")
    print(f"   Workers: {args.workers}")
    print("=" * 60)
    
    # Step 1: Enqueue companies
    print("\n📋 Step 1: Enqueuing companies...")
    from main_scraper.enqueue import enqueue_all
    count = enqueue_all(args.limit)
    
    if count == 0:
        print("❌ No companies to scrape. Run discovery first.")
        return
    
    # Step 2: Run workers
    print(f"\n🏃 Step 2: Running {args.workers} workers...")
    from main_scraper.run import WorkerManager
    manager = WorkerManager(args.workers, "jobs")
    manager.start_all()
    
    # Step 3: Show summary
    print("\n📊 Step 3: Summary")
    from main_scraper.config import OUTPUT_DIR
    
    total_files = 0
    total_jobs = 0
    total_with_desc = 0
    
    import json
    for ats in os.listdir(OUTPUT_DIR):
        ats_dir = os.path.join(OUTPUT_DIR, ats)
        if os.path.isdir(ats_dir):
            for f in os.listdir(ats_dir):
                if f.endswith('.json'):
                    total_files += 1
                    with open(os.path.join(ats_dir, f)) as fp:
                        data = json.load(fp)
                        jobs = data.get("jobs", [])
                        total_jobs += len(jobs)
                        total_with_desc += sum(1 for j in jobs if j.get("description"))
    
    print(f"   Companies scraped: {total_files}")
    print(f"   Total jobs: {total_jobs}")
    print(f"   Jobs with descriptions: {total_with_desc} ({100*total_with_desc/max(1,total_jobs):.1f}%)")
    print(f"   Output: {OUTPUT_DIR}/")
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
