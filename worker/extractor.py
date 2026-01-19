"""LLM-based job extraction with skill normalization."""

import json
import re
import os
import time
import random
from typing import Dict, Any, Optional, List
from openai import AzureOpenAI, RateLimitError
from dotenv import load_dotenv
from .normalizer import normalize_skills, normalize_tech_stack

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
) if AZURE_API_KEY and AZURE_ENDPOINT else None

# Extraction prompt for structured data
EXTRACTION_PROMPT = '''Extract structured data from this job posting. Return ONLY valid JSON.

Job Title: {title}
Company: {company}
Location: {location}

Description:
{description}

Extract and return this JSON structure:
{{
  "department": "Engineering|Sales|Marketing|Finance|HR|Design|Product|Operations|Legal|Customer Success|Other",
  "seniority": "Intern|Junior|Mid|Senior|Lead|Staff|Principal|Manager|Director|VP|C-Level",
  "tech_stack": ["list", "of", "technologies", "frameworks", "tools"],
  "skills": ["key", "skills", "required"],
  "pain_points": ["problems", "this", "role", "solves"],
  "job_summary": "One sentence describing the primary function of this role",
  "remote_policy": "Remote|Hybrid|Onsite|Unknown",
  "salary_min": null,
  "salary_max": null,
  "experience_years": null
}}

IMPORTANT:
- tech_stack: Only include specific technologies (Python, Kubernetes, AWS, etc.)
- skills: Include soft skills and domain expertise
- job_summary: Focus on the PRIMARY function, not a generic description
- Extract salary if mentioned (as integers, e.g., 150000)
- Return null for missing numeric fields

JSON:'''


def call_azure_openai(prompt: str, max_retries: int = 5) -> Optional[str]:
    """Call Azure OpenAI GPT-4o with exponential backoff for rate limits."""
    if not client:
        print("Azure OpenAI API key not set! Set AZURE_OPENAI_API_KEY env var.")
        return None
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a job posting analyzer. Extract structured data and return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1,
                model=AZURE_DEPLOYMENT
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            # Extract wait time from error message if available
            wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
            if "retry after" in str(e).lower():
                import re
                match = re.search(r'retry after (\d+)', str(e).lower())
                if match:
                    wait_time = max(int(match.group(1)), wait_time)
            
            if attempt < max_retries - 1:
                print(f"Rate limited, waiting {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"Rate limit exhausted after {max_retries} attempts")
                return None
        except Exception as e:
            print(f"Azure OpenAI error: {e}")
            return None
    
    return None


def extract_json(text: str) -> Optional[Dict]:
    """Extract JSON from LLM response."""
    if not text:
        return None
    
    # Try direct parse
    try:
        return json.loads(text.strip())
    except:
        pass
    
    # Try to find JSON in response
    patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested braces
        r'```json\s*(.*?)\s*```',  # Markdown code block
        r'```\s*(.*?)\s*```',  # Generic code block
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue
    
    return None


def extract_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured data from a job posting using LLM.
    
    Args:
        job: Raw job data with title, company, location, description
        
    Returns:
        Extracted structured data with normalized skills
    """
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    description = job.get("description", "")[:8000]  # Limit context
    
    if not description or len(description) < 100:
        return {"error": "No description", "raw": job}
    
    prompt = EXTRACTION_PROMPT.format(
        title=title,
        company=company,
        location=location,
        description=description
    )
    
    response = call_azure_openai(prompt)
    extracted = extract_json(response)
    
    if not extracted:
        return {"error": "Failed to parse LLM response", "raw": job}
    
    # Normalize skills and tech stack
    if "tech_stack" in extracted:
        extracted["tech_stack"] = normalize_tech_stack(extracted["tech_stack"])
    
    if "skills" in extracted:
        extracted["skills"] = normalize_skills(extracted["skills"])
    
    # Add original job metadata
    extracted["job_id"] = job.get("id", "")
    extracted["title"] = title
    extracted["company"] = company
    extracted["location"] = location
    extracted["url"] = job.get("url", "")
    
    return extracted


def batch_extract(jobs: List[Dict], batch_size: int = 10) -> List[Dict]:
    """
    Extract data from multiple jobs.
    
    For 50k scale, this would use:
    - Local models (Llama/Mistral) for initial filtering
    - GPT-4/Claude for complex extractions
    
    Current implementation uses single local model for simplicity.
    """
    results = []
    
    for i, job in enumerate(jobs):
        print(f"  Extracting {i+1}/{len(jobs)}: {job.get('title', 'Unknown')[:50]}")
        result = extract_job(job)
        results.append(result)
    
    return results
