"""Database connection and utilities."""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from .config import DATABASE_URL


# ============================================================================
# CENTRALIZED JOB FIELDS - Single source of truth for all job queries
# ============================================================================

JOB_FIELDS = [
    "id", "job_id", "company", "ats", "title", "location", "department",
    "seniority", "tech_stack", "skills", "pain_points", "remote_policy",
    "salary_min", "salary_max", "experience_years", "job_summary", "url"
]

JOB_FIELDS_SQL = ", ".join(JOB_FIELDS)


def format_job(job_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a job row to ensure all expected fields are present.
    Use this everywhere jobs are returned to guarantee consistent output.
    """
    return {
        "id": job_row.get("id"),
        "job_id": job_row.get("job_id", ""),
        "company": job_row.get("company", ""),
        "ats": job_row.get("ats", ""),
        "title": job_row.get("title", ""),
        "location": job_row.get("location", ""),
        "department": job_row.get("department"),
        "seniority": job_row.get("seniority"),
        "tech_stack": job_row.get("tech_stack") or [],
        "skills": job_row.get("skills") or [],
        "pain_points": job_row.get("pain_points") or [],
        "remote_policy": job_row.get("remote_policy"),
        "salary_min": job_row.get("salary_min"),
        "salary_max": job_row.get("salary_max"),
        "experience_years": job_row.get("experience_years"),
        "job_summary": job_row.get("job_summary", ""),
        "url": job_row.get("url", "")
    }


def format_jobs(job_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format a list of jobs."""
    return [format_job(j) for j in job_rows]


def get_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL)


@contextmanager
def get_cursor():
    """Context manager for database cursor."""
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def get_stats() -> Dict[str, Any]:
    """Get platform statistics."""
    with get_cursor() as cursor:
        # Total jobs
        cursor.execute("SELECT COUNT(*) as count FROM jobs")
        total_jobs = cursor.fetchone()["count"]
        
        # Jobs with parsed data
        cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE department IS NOT NULL")
        parsed_jobs = cursor.fetchone()["count"]
        
        # Unique companies
        cursor.execute("SELECT COUNT(DISTINCT company) as count FROM jobs")
        total_companies = cursor.fetchone()["count"]
        
        # Jobs by ATS
        cursor.execute("""
            SELECT ats, COUNT(*) as count 
            FROM jobs 
            GROUP BY ats 
            ORDER BY count DESC
        """)
        by_ats = {row["ats"]: row["count"] for row in cursor.fetchall()}
        
        # Top departments
        cursor.execute("""
            SELECT department, COUNT(*) as count 
            FROM jobs 
            WHERE department IS NOT NULL 
            GROUP BY department 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_departments = cursor.fetchall()
        
    return {
        "total_jobs": total_jobs,
        "parsed_jobs": parsed_jobs,
        "parse_rate": round(parsed_jobs / total_jobs * 100, 1) if total_jobs > 0 else 0,
        "total_companies": total_companies,
        "by_ats": by_ats,
        "top_departments": top_departments
    }


def search_jobs(
    query: Optional[str] = None,
    company: Optional[str] = None,
    department: Optional[str] = None,
    seniority: Optional[str] = None,
    tech_stack: Optional[List[str]] = None,
    remote_policy: Optional[str] = None,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Search jobs with filters."""
    conditions = []
    params = []
    
    if query:
        conditions.append("(title ILIKE %s OR raw_description ILIKE %s)")
        params.extend([f"%{query}%", f"%{query}%"])
    
    if company:
        conditions.append("company ILIKE %s")
        params.append(f"%{company}%")
    
    if department:
        conditions.append("department = %s")
        params.append(department)
    
    if seniority:
        conditions.append("seniority = %s")
        params.append(seniority)
    
    if tech_stack:
        conditions.append("tech_stack && %s")
        params.append(tech_stack)
    
    if remote_policy:
        conditions.append("remote_policy = %s")
        params.append(remote_policy)
    
    if salary_min:
        conditions.append("salary_max >= %s")
        params.append(salary_min)
    
    if salary_max:
        conditions.append("salary_min <= %s")
        params.append(salary_max)
    
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    
    with get_cursor() as cursor:
        # Get total count
        cursor.execute(f"SELECT COUNT(*) as count FROM jobs WHERE {where_clause}", params)
        total = cursor.fetchone()["count"]
        
        # Get results using centralized field list
        cursor.execute(f"""
            SELECT {JOB_FIELDS_SQL}
            FROM jobs 
            WHERE {where_clause}
            ORDER BY company, title
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        
        jobs = cursor.fetchall()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "jobs": format_jobs(jobs)
    }


def get_job_by_id(job_id: int) -> Optional[Dict]:
    """Get a single job by ID."""
    with get_cursor() as cursor:
        cursor.execute(f"""
            SELECT {JOB_FIELDS_SQL} FROM jobs WHERE id = %s
        """, [job_id])
        job = cursor.fetchone()
    
    return format_job(dict(job)) if job else None


def get_companies(
    search: Optional[str] = None,
    min_jobs: int = 1,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Get companies with job counts."""
    conditions = ["TRUE"]
    params = []
    
    if search:
        conditions.append("company ILIKE %s")
        params.append(f"%{search}%")
    
    where_clause = " AND ".join(conditions)
    
    with get_cursor() as cursor:
        cursor.execute(f"""
            SELECT company, ats, COUNT(*) as job_count,
                   array_agg(DISTINCT department) FILTER (WHERE department IS NOT NULL) as departments,
                   array_agg(DISTINCT seniority) FILTER (WHERE seniority IS NOT NULL) as seniorities
            FROM jobs
            WHERE {where_clause}
            GROUP BY company, ats
            HAVING COUNT(*) >= %s
            ORDER BY job_count DESC
            LIMIT %s OFFSET %s
        """, params + [min_jobs, limit, offset])
        
        companies = cursor.fetchall()
        
        # Get total
        cursor.execute(f"""
            SELECT COUNT(*) as count FROM (
                SELECT company FROM jobs WHERE {where_clause}
                GROUP BY company, ats HAVING COUNT(*) >= %s
            ) sub
        """, params + [min_jobs])
        total = cursor.fetchone()["count"]
    
    return {
        "total": total,
        "companies": [dict(c) for c in companies]
    }


def get_filter_options() -> Dict[str, List[str]]:
    """Get available filter options."""
    with get_cursor() as cursor:
        # Departments
        cursor.execute("""
            SELECT DISTINCT department FROM jobs 
            WHERE department IS NOT NULL 
            ORDER BY department
        """)
        departments = [r["department"] for r in cursor.fetchall()]
        
        # Seniority levels
        cursor.execute("""
            SELECT DISTINCT seniority FROM jobs 
            WHERE seniority IS NOT NULL 
            ORDER BY seniority
        """)
        seniorities = [r["seniority"] for r in cursor.fetchall()]
        
        # Remote policies
        cursor.execute("""
            SELECT DISTINCT remote_policy FROM jobs 
            WHERE remote_policy IS NOT NULL 
            ORDER BY remote_policy
        """)
        remote_policies = [r["remote_policy"] for r in cursor.fetchall()]
        
        # Top tech stack (most common)
        cursor.execute("""
            SELECT unnest(tech_stack) as tech, COUNT(*) as count
            FROM jobs 
            WHERE tech_stack IS NOT NULL
            GROUP BY tech
            ORDER BY count DESC
            LIMIT 50
        """)
        tech_stack = [r["tech"] for r in cursor.fetchall()]
    
    return {
        "departments": departments,
        "seniorities": seniorities,
        "remote_policies": remote_policies,
        "tech_stack": tech_stack
    }
