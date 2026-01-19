"""Natural Language to SQL query translator using Ollama."""

import json
import requests
from .config import OLLAMA_URL, OLLAMA_MODEL
from .connection import get_cursor

# Schema context for the LLM
SCHEMA_CONTEXT = """
PostgreSQL Database Schema:

TABLE jobs:
- id: SERIAL PRIMARY KEY
- job_id: VARCHAR(100) - unique job identifier
- company: VARCHAR(255) - company name (e.g., 'astronomer', 'stripe')
- ats: VARCHAR(50) - applicant tracking system ('greenhouse', 'lever', 'ashby', 'smartrecruiters')
- title: VARCHAR(500) - job title
- url: TEXT - job posting URL
- location: VARCHAR(255) - job location
- department: VARCHAR(100) - e.g., 'Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Design', 'Product', 'Operations'
- seniority: VARCHAR(50) - e.g., 'Intern', 'Junior', 'Mid', 'Senior', 'Lead', 'Manager', 'Director', 'VP', 'C-Level'
- tech_stack: TEXT[] - array of technologies (e.g., ARRAY['python', 'kubernetes', 'aws'])
- skills: TEXT[] - array of skills
- pain_points: TEXT[] - problems this role solves
- remote_policy: VARCHAR(50) - 'Remote', 'Hybrid', 'Onsite', 'Unknown'
- salary_min: INTEGER - minimum salary
- salary_max: INTEGER - maximum salary
- experience_years: INTEGER - required years of experience
- raw_description: TEXT - full job description

TABLE company_profiles:
- id: SERIAL PRIMARY KEY
- company: VARCHAR(255) - company name
- ats: VARCHAR(50)
- total_jobs: INTEGER - total job postings
- jobs_parsed: INTEGER - successfully parsed jobs
- parse_rate: FLOAT - parsing success rate
- departments: JSONB - department breakdown {"Engineering": 5, "Sales": 3}
- seniority_breakdown: JSONB - seniority distribution
- top_tech_stack: JSONB - top technologies with counts
- top_skills: JSONB - top skills with counts
- top_pain_points: JSONB - common pain points
- hiring_signals: TEXT[] - e.g., ARRAY['aggressive_hiring', 'ai_ml_focus', 'scaling_engineering']

ARRAY OPERATORS:
- 'value' = ANY(array_column) - check if value in array
- array_column @> ARRAY['val1', 'val2'] - array contains all values
- array_column && ARRAY['val1', 'val2'] - array overlaps (has any of values)
- array_length(array_column, 1) - get array length

JSONB OPERATORS:
- column->>'key' - get value as text
- column->'key' - get value as JSONB
- (column->>'key')::int - cast to integer
"""

NL_TO_SQL_PROMPT = """You are a PostgreSQL expert. Convert the natural language query to SQL.

{schema}

RULES:
1. Return ONLY the SQL query, no explanations
2. Use proper PostgreSQL syntax for arrays (ANY, @>, &&)
3. Use ILIKE for case-insensitive text matching
4. Always include reasonable LIMIT (default 20) unless counting
5. For tech stack queries, use lowercase: 'kubernetes' not 'Kubernetes'
6. When searching arrays, use && for "any of" and @> for "all of"

EXAMPLES:
- "companies hiring engineers" → SELECT DISTINCT company FROM jobs WHERE department = 'Engineering' LIMIT 20;
- "jobs with kubernetes" → SELECT company, title FROM jobs WHERE 'kubernetes' = ANY(tech_stack) LIMIT 20;
- "senior roles at stripe" → SELECT title, department FROM jobs WHERE company ILIKE '%stripe%' AND seniority = 'Senior' LIMIT 20;
- "companies with ai focus" → SELECT company, hiring_signals FROM company_profiles WHERE 'ai_ml_focus' = ANY(hiring_signals);
- "remote python jobs" → SELECT company, title FROM jobs WHERE remote_policy = 'Remote' AND 'python' = ANY(tech_stack) LIMIT 20;
- "top 10 companies by job count" → SELECT company, total_jobs FROM company_profiles ORDER BY total_jobs DESC LIMIT 10;

USER QUERY: {query}

SQL:"""


def nl_to_sql(natural_query: str) -> str:
    """Convert natural language to SQL using Ollama."""
    prompt = NL_TO_SQL_PROMPT.format(
        schema=SCHEMA_CONTEXT,
        query=natural_query
    )
    
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,  # Deterministic for SQL
                "num_predict": 500
            }
        },
        timeout=60
    )
    
    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.text}")
    
    result = response.json().get("response", "").strip()
    
    # Clean up the response
    # Remove markdown code blocks if present
    if result.startswith("```"):
        lines = result.split("\n")
        result = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    
    # Remove any leading/trailing whitespace or semicolons issues
    result = result.strip()
    if not result.endswith(";"):
        result += ";"
    
    return result


def execute_query(sql: str) -> list:
    """Execute SQL and return results."""
    with get_cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


def ask(natural_query: str, show_sql: bool = True) -> list:
    """
    Main interface: Ask a question in natural language, get results.
    
    Args:
        natural_query: Natural language question
        show_sql: Whether to print the generated SQL
    
    Returns:
        List of result dictionaries
    """
    print(f"\n🔍 Query: {natural_query}")
    
    # Convert to SQL
    sql = nl_to_sql(natural_query)
    
    if show_sql:
        print(f"📝 SQL: {sql}")
    
    # Execute
    try:
        results = execute_query(sql)
        print(f"✅ Found {len(results)} results\n")
        return results
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        print(f"   Generated SQL: {sql}")
        return []


def interactive():
    """Interactive query mode."""
    print("=" * 60)
    print("🔍 GTM Intelligence Query Interface")
    print("=" * 60)
    print("Ask questions in natural language. Type 'exit' to quit.\n")
    print("Examples:")
    print("  - Companies hiring for AI/ML roles")
    print("  - Remote senior engineering jobs")
    print("  - Top 10 companies by job count")
    print("  - Jobs at Stripe with Python")
    print("=" * 60)
    
    while True:
        try:
            query = input("\n❓ Your question: ").strip()
            
            if query.lower() in ("exit", "quit", "q"):
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            results = ask(query)
            
            # Pretty print results
            if results:
                for i, row in enumerate(results[:10], 1):
                    print(f"{i}. {dict(row)}")
                
                if len(results) > 10:
                    print(f"   ... and {len(results) - 10} more")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    interactive()
