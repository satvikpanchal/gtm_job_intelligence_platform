"""Jobs API routes."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..db import search_jobs, get_job_by_id, get_filter_options

router = APIRouter()


@router.get("")
async def list_jobs(
    q: Optional[str] = Query(None, description="Search query for title/description"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    department: Optional[str] = Query(None, description="Filter by department"),
    seniority: Optional[str] = Query(None, description="Filter by seniority level"),
    tech: Optional[List[str]] = Query(None, description="Filter by tech stack"),
    remote: Optional[str] = Query(None, description="Filter by remote policy"),
    salary_min: Optional[int] = Query(None, description="Minimum salary"),
    salary_max: Optional[int] = Query(None, description="Maximum salary"),
    limit: int = Query(10000, ge=1, le=20000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Search and filter jobs.
    
    Examples:
    - /api/jobs?q=engineer&department=Engineering
    - /api/jobs?company=stripe&seniority=Senior
    - /api/jobs?tech=python&tech=kubernetes&remote=Remote
    - /api/jobs?salary_min=150000
    """
    return search_jobs(
        query=q,
        company=company,
        department=department,
        seniority=seniority,
        tech_stack=tech,
        remote_policy=remote,
        salary_min=salary_min,
        salary_max=salary_max,
        limit=limit,
        offset=offset
    )


@router.get("/filters")
async def get_filters():
    """Get available filter options for dropdowns."""
    return get_filter_options()


@router.get("/{job_id}")
async def get_job(job_id: int):
    """Get a single job by ID."""
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
