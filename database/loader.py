"""Load JSON files into PostgreSQL."""

import os
import json
from pathlib import Path
from datetime import datetime
from .connection import get_cursor

# Paths
SCRAPED_DIR = Path(__file__).parent.parent / "data" / "scraped"
EXTRACTED_DIR = Path(__file__).parent.parent / "data" / "extracted"
PROFILES_DIR = Path(__file__).parent.parent / "data" / "profiles"


def load_jobs():
    """Load all scraped jobs into the database."""
    total_loaded = 0
    
    for ats_dir in SCRAPED_DIR.iterdir():
        if not ats_dir.is_dir():
            continue
        
        ats = ats_dir.name
        
        for json_file in ats_dir.glob("*.json"):
            company = json_file.stem
            
            with open(json_file) as f:
                data = json.load(f)
            
            jobs = data.get("jobs", [])
            
            with get_cursor() as cursor:
                for job in jobs:
                    cursor.execute("""
                        INSERT INTO jobs (job_id, company, ats, title, url, location, raw_description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (ats, company, job_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            url = EXCLUDED.url,
                            location = EXCLUDED.location,
                            raw_description = EXCLUDED.raw_description
                    """, (
                        job.get("id", ""),
                        company,
                        ats,
                        job.get("title", ""),
                        job.get("url", ""),
                        job.get("location", ""),
                        job.get("description", "")
                    ))
                    total_loaded += 1
            
            print(f"  Loaded {len(jobs)} jobs from {ats}/{company}")
    
    print(f"\n✅ Total jobs loaded: {total_loaded}")
    return total_loaded


def load_parsed_jobs():
    """Load LLM-parsed job data into the database."""
    if not EXTRACTED_DIR.exists():
        print("⚠️  No extracted jobs found. Run extraction workers first.")
        return 0
    
    total_inserted = 0
    total_skipped = 0
    
    for ats_dir in EXTRACTED_DIR.iterdir():
        if not ats_dir.is_dir():
            continue
        
        ats = ats_dir.name
        
        for json_file in ats_dir.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)
            
            company = data.get("company", json_file.stem)
            jobs = data.get("jobs", [])
            
            with get_cursor() as cursor:
                for job in jobs:
                    if "error" in job:
                        total_skipped += 1
                        continue
                    
                    cursor.execute("""
                        INSERT INTO jobs (
                            job_id, company, ats, title, url, location,
                            department, seniority, tech_stack, skills, pain_points,
                            remote_policy, salary_min, salary_max, experience_years,
                            job_summary, parsed_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (ats, company, job_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            url = EXCLUDED.url,
                            location = EXCLUDED.location,
                            department = EXCLUDED.department,
                            seniority = EXCLUDED.seniority,
                            tech_stack = EXCLUDED.tech_stack,
                            skills = EXCLUDED.skills,
                            pain_points = EXCLUDED.pain_points,
                            remote_policy = EXCLUDED.remote_policy,
                            salary_min = EXCLUDED.salary_min,
                            salary_max = EXCLUDED.salary_max,
                            experience_years = EXCLUDED.experience_years,
                            job_summary = EXCLUDED.job_summary,
                            parsed_at = EXCLUDED.parsed_at
                    """, (
                        job.get("job_id", ""),
                        company,
                        ats,
                        job.get("title", ""),
                        job.get("url", ""),
                        job.get("location", ""),
                        job.get("department"),
                        job.get("seniority"),
                        job.get("tech_stack", []),
                        job.get("skills", []),
                        job.get("pain_points", []),
                        job.get("remote_policy"),
                        job.get("salary_min"),
                        job.get("salary_max"),
                        job.get("experience_years"),
                        job.get("job_summary"),
                        datetime.now()
                    ))
                    total_inserted += 1
            
            print(f"  Loaded {len(jobs)} jobs for {ats}/{company}")
    
    print(f"\n✅ Total jobs inserted: {total_inserted} (skipped {total_skipped} with errors)")
    return total_inserted


def load_company_profiles():
    """Load company profiles into the database."""
    if not PROFILES_DIR.exists():
        print("⚠️  No company profiles found. Run analysis first.")
        return 0
    
    total_loaded = 0
    
    for json_file in PROFILES_DIR.glob("*.json"):
        with open(json_file) as f:
            profile = json.load(f)
        
        # Parse filename: ats_company.json
        parts = json_file.stem.split("_", 1)
        if len(parts) != 2:
            continue
        
        ats, company = parts
        
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO company_profiles (
                    company, ats, total_jobs, jobs_parsed, parse_rate,
                    departments, seniority_breakdown, top_tech_stack,
                    top_skills, top_pain_points, hiring_signals
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ats, company) DO UPDATE SET
                    total_jobs = EXCLUDED.total_jobs,
                    jobs_parsed = EXCLUDED.jobs_parsed,
                    parse_rate = EXCLUDED.parse_rate,
                    departments = EXCLUDED.departments,
                    seniority_breakdown = EXCLUDED.seniority_breakdown,
                    top_tech_stack = EXCLUDED.top_tech_stack,
                    top_skills = EXCLUDED.top_skills,
                    top_pain_points = EXCLUDED.top_pain_points,
                    hiring_signals = EXCLUDED.hiring_signals,
                    analyzed_at = NOW()
            """, (
                company,
                ats,
                profile.get("total_jobs", 0),
                profile.get("jobs_parsed", 0),
                profile.get("parse_rate", 0),
                json.dumps(profile.get("departments", {})),
                json.dumps(profile.get("seniority", {})),
                json.dumps(profile.get("tech_stack", [])),
                json.dumps(profile.get("skills", [])),
                json.dumps(profile.get("pain_points", [])),
                profile.get("hiring_signals", [])
            ))
            total_loaded += 1
        
        print(f"  Loaded profile: {ats}/{company}")
    
    print(f"\n✅ Total profiles loaded: {total_loaded}")
    return total_loaded


def load_all():
    """Load everything into the database."""
    print("📦 Loading scraped jobs...")
    load_jobs()
    
    print("\n🧠 Loading parsed job data...")
    load_parsed_jobs()
    
    print("\n📊 Loading company profiles...")
    load_company_profiles()
    
    print("\n✅ All data loaded!")


if __name__ == "__main__":
    load_all()
