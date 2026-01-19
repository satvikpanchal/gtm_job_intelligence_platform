#!/usr/bin/env python3
"""Show summary of scraped jobs."""

import os
import json

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "final_jobs_scraped")

def main():
    total_files = 0
    total_jobs = 0
    total_with_desc = 0
    by_ats = {}

    for ats in os.listdir(OUTPUT_DIR):
        ats_dir = os.path.join(OUTPUT_DIR, ats)
        if os.path.isdir(ats_dir):
            by_ats[ats] = {"companies": 0, "jobs": 0, "with_desc": 0}
            for f in os.listdir(ats_dir):
                if f.endswith(".json"):
                    total_files += 1
                    by_ats[ats]["companies"] += 1
                    with open(os.path.join(ats_dir, f)) as fp:
                        data = json.load(fp)
                        jobs = data.get("jobs", [])
                        total_jobs += len(jobs)
                        by_ats[ats]["jobs"] += len(jobs)
                        with_desc = sum(1 for j in jobs if j.get("description"))
                        total_with_desc += with_desc
                        by_ats[ats]["with_desc"] += with_desc

    print("=" * 65)
    print("SCRAPING RESULTS")
    print("=" * 65)
    print()
    print(f"ATS                  Companies       Jobs   With Desc     Rate")
    print("-" * 65)
    for ats, stats in sorted(by_ats.items()):
        rate = 100 * stats["with_desc"] / max(1, stats["jobs"])
        print(f"{ats:20} {stats['companies']:>9} {stats['jobs']:>10} {stats['with_desc']:>11} {rate:>8.1f}%")
    print("-" * 65)
    rate = 100 * total_with_desc / max(1, total_jobs)
    print(f"{'TOTAL':20} {total_files:>9} {total_jobs:>10} {total_with_desc:>11} {rate:>8.1f}%")
    print()
    print(f"Output: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
