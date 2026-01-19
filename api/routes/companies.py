"""Companies API routes."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..db import get_companies, get_cursor

router = APIRouter()


@router.get("")
async def list_companies(
    q: Optional[str] = Query(None, description="Search company name"),
    min_jobs: int = Query(1, ge=1, description="Minimum job count"),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0)
):
    """
    List companies with job counts.
    
    Examples:
    - /api/companies?q=stripe
    - /api/companies?min_jobs=10
    """
    return get_companies(
        search=q,
        min_jobs=min_jobs,
        limit=limit,
        offset=offset
    )


@router.get("/{company_name}")
async def get_company(company_name: str):
    """Get detailed company profile."""
    with get_cursor() as cursor:
        # Get company jobs summary
        cursor.execute("""
            SELECT 
                company,
                ats,
                COUNT(*) as total_jobs,
                COUNT(*) FILTER (WHERE department IS NOT NULL) as parsed_jobs,
                array_agg(DISTINCT department) FILTER (WHERE department IS NOT NULL) as departments,
                array_agg(DISTINCT seniority) FILTER (WHERE seniority IS NOT NULL) as seniorities
            FROM jobs
            WHERE company ILIKE %s
            GROUP BY company, ats
        """, [f"%{company_name}%"])
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_data = dict(result)
        
        # Get tech stack breakdown
        cursor.execute("""
            SELECT unnest(tech_stack) as tech, COUNT(*) as count
            FROM jobs
            WHERE company ILIKE %s AND tech_stack IS NOT NULL
            GROUP BY tech
            ORDER BY count DESC
            LIMIT 20
        """, [f"%{company_name}%"])
        
        company_data["tech_stack"] = [
            {"tech": r["tech"], "count": r["count"]} 
            for r in cursor.fetchall()
        ]
        
        # Get department breakdown
        cursor.execute("""
            SELECT department, COUNT(*) as count
            FROM jobs
            WHERE company ILIKE %s AND department IS NOT NULL
            GROUP BY department
            ORDER BY count DESC
        """, [f"%{company_name}%"])
        
        company_data["department_breakdown"] = [
            {"department": r["department"], "count": r["count"]}
            for r in cursor.fetchall()
        ]
        
        # Get seniority breakdown
        cursor.execute("""
            SELECT seniority, COUNT(*) as count
            FROM jobs
            WHERE company ILIKE %s AND seniority IS NOT NULL
            GROUP BY seniority
            ORDER BY count DESC
        """, [f"%{company_name}%"])
        
        company_data["seniority_breakdown"] = [
            {"seniority": r["seniority"], "count": r["count"]}
            for r in cursor.fetchall()
        ]
        
        # Get sample jobs
        cursor.execute("""
            SELECT id, title, department, seniority, location, remote_policy
            FROM jobs
            WHERE company ILIKE %s
            ORDER BY title
            LIMIT 10
        """, [f"%{company_name}%"])
        
        company_data["sample_jobs"] = [dict(r) for r in cursor.fetchall()]
    
    return company_data


@router.get("/{company_name}/jobs")
async def get_company_jobs(
    company_name: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get all jobs for a company."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, job_id, title, department, seniority, location,
                   tech_stack, skills, remote_policy, salary_min, salary_max, url
            FROM jobs
            WHERE company ILIKE %s
            ORDER BY department, seniority, title
            LIMIT %s OFFSET %s
        """, [f"%{company_name}%", limit, offset])
        
        jobs = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM jobs WHERE company ILIKE %s
        """, [f"%{company_name}%"])
        total = cursor.fetchone()["count"]
    
    return {
        "company": company_name,
        "total": total,
        "jobs": jobs
    }
