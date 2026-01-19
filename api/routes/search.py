"""Natural language search using Azure OpenAI LLM-to-SQL."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import re
import json
from openai import AzureOpenAI
from ..config import AZURE_ENDPOINT, AZURE_API_KEY, AZURE_API_VERSION, AZURE_DEPLOYMENT
from ..db import get_cursor, JOB_FIELDS_SQL, JOB_FIELDS, format_job, format_jobs

router = APIRouter()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
)

# Schema context for LLM
SCHEMA_CONTEXT = """
PostgreSQL Database Schema:

TABLE jobs:
- id: SERIAL PRIMARY KEY
- job_id: VARCHAR - unique job identifier
- company: TEXT - company name (e.g., 'stripe', 'openai')
- ats: VARCHAR(50) - ATS platform ('greenhouse', 'lever', 'ashby')
- title: TEXT - job title
- url: TEXT - job posting URL
- location: TEXT - job location
- department: VARCHAR(100) - 'Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Design', 'Product', 'Operations'
- seniority: VARCHAR(50) - 'Intern', 'Junior', 'Mid', 'Senior', 'Lead', 'Staff', 'Principal', 'Manager', 'Director', 'VP', 'C-Level'
- tech_stack: TEXT[] - array of technologies (e.g., ARRAY['python', 'kubernetes'])
- skills: TEXT[] - array of skills
- pain_points: TEXT[] - problems this role solves
- remote_policy: VARCHAR(50) - 'Remote', 'Hybrid', 'Onsite', 'Unknown'
- salary_min: INTEGER - minimum salary
- salary_max: INTEGER - maximum salary
- experience_years: INTEGER

ARRAY OPERATORS:
- 'value' = ANY(array_column) - check if value in array
- array_column && ARRAY['val1', 'val2'] - array overlaps (has any of values)
- array_column @> ARRAY['val1', 'val2'] - array contains all values
"""

NL_TO_SQL_PROMPT = """Convert this natural language query to PostgreSQL.

{schema}

RULES:
1. Return ONLY the SQL query, no explanations
2. Use ILIKE for case-insensitive text matching
3. Do NOT add any LIMIT unless the user explicitly asks for a specific number of results
4. For tech stack queries, use lowercase and && operator
5. Always SELECT these columns: {job_fields}
6. Add WHERE/ORDER BY based on the query intent

USER QUERY: {query}

SQL:"""


class NLSearchRequest(BaseModel):
    query: str
    limit: int = 50


class NLSearchResponse(BaseModel):
    query: str
    sql: str
    results: List[Dict[str, Any]]
    total: int


def nl_to_sql(query: str) -> str:
    """Convert natural language to SQL using Azure OpenAI."""
    prompt = NL_TO_SQL_PROMPT.format(
        schema=SCHEMA_CONTEXT,
        job_fields=JOB_FIELDS_SQL,
        query=query
    )
    
    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a PostgreSQL expert. Return ONLY valid SQL queries, no explanations or markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=500
    )
    
    result = response.choices[0].message.content.strip()
    
    # Clean up response
    if result.startswith("```"):
        lines = result.split("\n")
        result = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    
    result = result.strip()
    if not result.endswith(";"):
        result += ";"
    
    return result


@router.post("/nl", response_model=NLSearchResponse)
async def natural_language_search(request: NLSearchRequest):
    """
    Search using natural language.
    
    Examples:
    - "Show me all Staff roles paying >$200k in NYC"
    - "Companies hiring for AI/ML engineers"
    - "Remote senior engineering jobs"
    - "Top 10 companies by job count"
    """
    try:
        sql = nl_to_sql(request.query)
        
        with get_cursor() as cursor:
            cursor.execute(sql)
            results = [dict(r) for r in cursor.fetchall()]
        
        return NLSearchResponse(
            query=request.query,
            sql=sql,
            results=results,
            total=len(results)
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query error: {str(e)}")


@router.get("/nl")
async def nl_search_get(
    q: str = Query(..., description="Natural language query")
):
    """GET version of natural language search."""
    result = await natural_language_search(NLSearchRequest(query=q))
    
    # Use centralized format_jobs for consistent output
    normalized = format_jobs(result.results)
    
    return {
        "query": result.query,
        "sql": result.sql,
        "results": normalized,
        "total": result.total
    }


@router.get("/tech-trends")
async def tech_trends(limit: int = Query(20, ge=1, le=100)):
    """Get most common technologies across all jobs."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT unnest(tech_stack) as tech, COUNT(*) as count
            FROM jobs 
            WHERE tech_stack IS NOT NULL
            GROUP BY tech
            ORDER BY count DESC
            LIMIT %s
        """, [limit])
        
        return [dict(r) for r in cursor.fetchall()]


@router.get("/hiring-signals")
async def hiring_signals():
    """Get companies with strong hiring signals."""
    with get_cursor() as cursor:
        # Companies with most job postings
        cursor.execute("""
            SELECT company, COUNT(*) as job_count,
                   COUNT(*) FILTER (WHERE department = 'Engineering') as eng_count,
                   COUNT(*) FILTER (WHERE department = 'Sales') as sales_count,
                   COUNT(*) FILTER (WHERE seniority IN ('Senior', 'Staff', 'Principal')) as senior_count
            FROM jobs
            GROUP BY company
            HAVING COUNT(*) >= 10
            ORDER BY job_count DESC
            LIMIT 50
        """)
        
        companies = []
        for row in cursor.fetchall():
            signals = []
            if row["job_count"] >= 50:
                signals.append("aggressive_hiring")
            if row["eng_count"] >= 10:
                signals.append("scaling_engineering")
            if row["sales_count"] >= 5:
                signals.append("gtm_expansion")
            if row["senior_count"] >= 5:
                signals.append("building_leadership")
            
            companies.append({
                "company": row["company"],
                "job_count": row["job_count"],
                "eng_count": row["eng_count"],
                "sales_count": row["sales_count"],
                "senior_count": row["senior_count"],
                "signals": signals
            })
        
        return companies


# Resume Matching Feature
RESUME_MATCH_PROMPT = """You are an expert recruiter and career advisor. Analyze this resume and compare it against the provided job listings.

RESUME:
{resume_text}

JOBS TO COMPARE ({job_count} jobs):
{jobs_summary}

For each job, calculate a match score from 0-100 based on:
- Skills alignment (40% weight): How well do the candidate's skills match the required skills and tech stack?
- Experience level (30% weight): Does the candidate's experience level match the seniority?
- Domain fit (20% weight): Is the candidate's background relevant to the department/industry?
- Overall potential (10% weight): Could this person grow into the role?

Return ONLY the TOP 10 best matching jobs as a valid JSON array with this structure:
[
  {{
    "job_id": <id>,
    "match_score": <0-100>,
    "matching_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3", "skill4"],
    "summary": "One sentence explaining the match"
  }}
]

Be strict but fair. A 90+ score means near-perfect match. 70-89 is strong. 50-69 is moderate. Below 50 is weak.
Return results sorted by match_score descending."""


@router.post("/resume-match")
async def match_resume_to_jobs(
    resume: UploadFile = File(...),
    job_ids: str = Form(...)  # Comma-separated job IDs
):
    """
    Upload a resume and get match scores against specific jobs.
    
    - resume: PDF or text file of the resume
    - job_ids: Comma-separated list of job IDs to compare against
    """
    import PyPDF2
    import io
    
    # Read resume content
    content = await resume.read()
    resume_text = ""
    
    if resume.filename.endswith('.pdf'):
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                resume_text += page.extract_text() + "\n"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not parse PDF: {str(e)}")
    else:
        # Assume text file
        resume_text = content.decode('utf-8', errors='ignore')
    
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume")
    
    # Parse job IDs
    try:
        ids = [int(id.strip()) for id in job_ids.split(',') if id.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job IDs format")
    
    if not ids:
        raise HTTPException(status_code=400, detail="No job IDs provided")
    
    # Fetch jobs from database using centralized field list
    with get_cursor() as cursor:
        placeholders = ','.join(['%s'] * len(ids))
        cursor.execute(f"""
            SELECT {JOB_FIELDS_SQL}
            FROM jobs 
            WHERE id IN ({placeholders})
        """, ids)
        jobs = format_jobs(cursor.fetchall())
    
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found with provided IDs")
    
    # Build jobs summary for LLM
    jobs_summary = ""
    for job in jobs:
        jobs_summary += f"""
---
ID: {job['id']}
Title: {job['title']} at {job['company']}
Location: {job['location']} | Remote: {job['remote_policy']}
Department: {job['department']} | Level: {job['seniority']}
Experience Required: {job['experience_years']} years
Tech Stack: {', '.join(job['tech_stack'] or [])}
Skills: {', '.join(job['skills'] or [])}
Summary: {job['job_summary']}
"""
    
    # Call Azure OpenAI for matching
    prompt = RESUME_MATCH_PROMPT.format(
        resume_text=resume_text[:8000],  # Limit resume text
        job_count=len(jobs),
        jobs_summary=jobs_summary[:12000]  # Limit jobs text
    )
    
    try:
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an expert recruiter. Return ONLY valid JSON arrays, no markdown or explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean up response
        if result_text.startswith("```"):
            lines = result_text.split("\n")
            result_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        matches = json.loads(result_text)
        
        # Enrich with ALL job details using centralized format_job
        job_map = {j['id']: j for j in jobs}
        enriched_matches = []
        for match in matches:
            job = job_map.get(match['job_id'], {})
            enriched = format_job(job) if job else {}
            enriched['match_score'] = match.get('match_score', 0)
            enriched['matching_skills'] = match.get('matching_skills', [])
            enriched['missing_skills'] = match.get('missing_skills', [])
            enriched['summary'] = match.get('summary', '')
            enriched_matches.append(enriched)
        
        # Return only top 10 matches
        top_matches = sorted(enriched_matches, key=lambda x: x.get('match_score', 0), reverse=True)[:10]
        
        return {
            "resume_filename": resume.filename,
            "jobs_analyzed": len(jobs),
            "matches": top_matches
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI matching failed: {str(e)}")


@router.post("/resume-match-all")
async def match_resume_to_search(
    resume: UploadFile = File(...),
    query: str = Form(None),
    company: str = Form(None),
    department: str = Form(None),
    seniority: str = Form(None),
    limit: int = Form(20)
):
    """
    Upload a resume and get match scores against jobs matching search criteria.
    If no filters provided, matches against top 20 jobs.
    """
    import PyPDF2
    import io
    
    # Read resume content
    content = await resume.read()
    resume_text = ""
    
    if resume.filename.endswith('.pdf'):
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                resume_text += page.extract_text() + "\n"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not parse PDF: {str(e)}")
    else:
        resume_text = content.decode('utf-8', errors='ignore')
    
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume")
    
    # Build query
    conditions = []
    params = []
    
    if query:
        conditions.append("(title ILIKE %s OR job_summary ILIKE %s)")
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
    
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    
    with get_cursor() as cursor:
        cursor.execute(f"""
            SELECT {JOB_FIELDS_SQL}
            FROM jobs 
            WHERE {where_clause}
            LIMIT %s
        """, params + [limit])
        jobs = format_jobs(cursor.fetchall())
    
    if not jobs:
        return {"resume_filename": resume.filename, "jobs_analyzed": 0, "matches": []}
    
    # Build jobs summary for LLM
    jobs_summary = ""
    for job in jobs:
        jobs_summary += f"""
---
ID: {job['id']}
Title: {job['title']} at {job['company']}
Location: {job['location']} | Remote: {job['remote_policy']}
Department: {job['department']} | Level: {job['seniority']}
Experience Required: {job['experience_years']} years
Tech Stack: {', '.join(job['tech_stack'] or [])}
Skills: {', '.join(job['skills'] or [])}
Summary: {job['job_summary']}
"""
    
    prompt = RESUME_MATCH_PROMPT.format(
        resume_text=resume_text[:8000],
        job_count=len(jobs),
        jobs_summary=jobs_summary[:12000]
    )
    
    try:
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an expert recruiter. Return ONLY valid JSON arrays, no markdown or explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        if result_text.startswith("```"):
            lines = result_text.split("\n")
            result_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        matches = json.loads(result_text)
        
        # Enrich with ALL job details using centralized format_job
        job_map = {j['id']: j for j in jobs}
        enriched_matches = []
        for match in matches:
            job = job_map.get(match['job_id'], {})
            enriched = format_job(job) if job else {}
            enriched['match_score'] = match.get('match_score', 0)
            enriched['matching_skills'] = match.get('matching_skills', [])
            enriched['missing_skills'] = match.get('missing_skills', [])
            enriched['summary'] = match.get('summary', '')
            enriched_matches.append(enriched)
        
        # Return only top 10 matches
        top_matches = sorted(enriched_matches, key=lambda x: x.get('match_score', 0), reverse=True)[:10]
        
        return {
            "resume_filename": resume.filename,
            "jobs_analyzed": len(jobs),
            "matches": top_matches
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI matching failed: {str(e)}")
