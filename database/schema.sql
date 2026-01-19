-- GTM Intelligence Platform Schema

-- Jobs table: individual job postings
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL,
    company VARCHAR(255) NOT NULL,
    ats VARCHAR(50) NOT NULL,  -- greenhouse, lever, ashby, smartrecruiters
    title VARCHAR(500) NOT NULL,
    url TEXT,
    location VARCHAR(255),
    
    -- LLM-extracted fields
    department VARCHAR(100),
    seniority VARCHAR(50),
    tech_stack TEXT[],  -- Array of technologies
    skills TEXT[],
    pain_points TEXT[],
    remote_policy VARCHAR(50),
    salary_min INTEGER,
    salary_max INTEGER,
    experience_years INTEGER,
    job_summary TEXT,
    
    -- Metadata
    raw_description TEXT,
    scraped_at TIMESTAMP DEFAULT NOW(),
    parsed_at TIMESTAMP,
    
    UNIQUE(ats, company, job_id)
);

-- Company profiles: aggregated insights per company
CREATE TABLE IF NOT EXISTS company_profiles (
    id SERIAL PRIMARY KEY,
    company VARCHAR(255) NOT NULL,
    ats VARCHAR(50) NOT NULL,
    
    -- Aggregated stats
    total_jobs INTEGER DEFAULT 0,
    jobs_parsed INTEGER DEFAULT 0,
    parse_rate FLOAT,
    
    -- Department breakdown (JSONB for flexibility)
    departments JSONB,  -- {"Engineering": 5, "Sales": 3}
    seniority_breakdown JSONB,
    
    -- Top technologies (sorted by frequency)
    top_tech_stack JSONB,  -- [{"tech": "python", "count": 10}, ...]
    top_skills JSONB,
    top_pain_points JSONB,
    
    -- Hiring signals
    hiring_signals TEXT[],  -- ["aggressive_hiring", "ai_ml_focus"]
    
    -- Metadata
    analyzed_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(ats, company)
);

-- Indexes for fast filtering
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_department ON jobs(department);
CREATE INDEX IF NOT EXISTS idx_jobs_seniority ON jobs(seniority);
CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(remote_policy);
CREATE INDEX IF NOT EXISTS idx_jobs_tech_stack ON jobs USING GIN(tech_stack);
CREATE INDEX IF NOT EXISTS idx_jobs_skills ON jobs USING GIN(skills);

CREATE INDEX IF NOT EXISTS idx_profiles_company ON company_profiles(company);
CREATE INDEX IF NOT EXISTS idx_profiles_signals ON company_profiles USING GIN(hiring_signals);
