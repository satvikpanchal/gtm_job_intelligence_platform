# 🎯 GTM Job Intelligence Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![OpenAI](https://img.shields.io/badge/Azure_OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Alpine.js](https://img.shields.io/badge/Alpine.js-8BC0D0?style=for-the-badge&logo=alpine.js&logoColor=black)

**A production-grade job intelligence system that scrapes, extracts, and analyzes job postings from major ATS platforms using LLM-powered data extraction.**

[Features](#-features) • [Demo](#-demo) • [Architecture](#-architecture) • [Setup](#-setup) • [Technical Deep-Dive](#-technical-deep-dive)

</div>

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| **Total Jobs Scraped** | 14,592 |
| **Companies Tracked** | 144 |
| **ATS Platforms** | 4 (Greenhouse, Lever, Ashby, SmartRecruiters) |
| **LLM Processing Cost** | ~$45 USD |
| **Fields Extracted per Job** | 17 |

---

## ✨ Features

### 🔍 Smart Job Search
- **Multi-filter Search** — Filter by company, department, seniority, tech stack, remote policy, and salary range
- **Real-time Results** — Instant search across 14k+ jobs
- **Rich Job Cards** — Tech stack badges, salary display with currency detection, department tags

### 🤖 AI-Powered Natural Language Search
- **Ask in Plain English** — "Show me senior Python engineers at fintech companies paying over $200k"
- **LLM-to-SQL Translation** — GPT-4o converts your query to optimized PostgreSQL
- **Intelligent Understanding** — Handles synonyms, fuzzy matching, and complex multi-condition queries

### 📄 Resume Matching
- **Upload Your Resume** — PDF or text format
- **AI Match Scoring** — Get 0-100 match scores against jobs
- **Skills Gap Analysis** — See matching skills and what you're missing
- **Top 10 Recommendations** — Sorted by best fit

### 🏢 Company Intelligence
- **Company Browser** — Browse all tracked companies with job counts
- **Department Breakdown** — See hiring focus across Engineering, Sales, Product, etc.
- **Hiring Signals** — Identify companies scaling aggressively

---

## 🎬 Demo

### Main Job Search
> *Filter and search across 14,592 jobs with rich metadata*

<img src="docs/screenshots/job-search.png" alt="Job Search Demo" width="700">

---

### AI-Powered Search
> *Ask questions in natural language — the AI writes the SQL for you*

<img src="docs/screenshots/ai-search.png" alt="AI Search Demo" width="700">

---

### Job Details View
> *Full job information with tech stack, skills, pain points, and more*

<img src="docs/screenshots/job-details.png" alt="Job Details Demo" width="700">

---

### Resume Matching
> *Upload your resume and get AI-powered match scores*

<img src="docs/screenshots/resume-match.png" alt="Resume Match Demo" width="700">

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GTM Job Intelligence Platform                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │  Greenhouse  │     │    Lever     │     │    Ashby     │                │
│  │     API      │     │     API      │     │     API      │                │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘                │
│         │                    │                    │                         │
│         └────────────────────┼────────────────────┘                         │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SCRAPER (Python + Redis Queue)                  │   │
│  │  • Proxy Rotation (10 residential proxies)                          │   │
│  │  • User-Agent Randomization                                          │   │
│  │  • Rate Limiting & Exponential Backoff                               │   │
│  │  • Parallel Workers (50 concurrent)                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      EXTRACTOR (GPT-4o via Azure OpenAI)             │   │
│  │  • Batch Processing (20 jobs/batch)                                  │   │
│  │  • Structured JSON Output                                            │   │
│  │  • 17 Fields Extracted per Job                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      PostgreSQL 15                                    │   │
│  │  • 14,592 Jobs  •  144 Companies  •  Full-text Search Indexes        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Backend                                  │   │
│  │  • REST API  •  NL-to-SQL Search  •  Resume Matching                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Frontend (Alpine.js + Tailwind CSS)             │   │
│  │  • Glass Morphism UI  •  Real-time Filters  •  Responsive            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Scraping** | Python, Requests, BeautifulSoup, Redis Queue (RQ) |
| **Proxy Infrastructure** | Residential Proxy Pool, Rotating User-Agents |
| **LLM Processing** | Azure OpenAI (GPT-4o), structured JSON extraction |
| **Database** | PostgreSQL 15, psycopg2, Full-text Search |
| **Backend API** | FastAPI, Pydantic, Uvicorn |
| **Frontend** | Alpine.js, Tailwind CSS, Glass Morphism Design |
| **Infrastructure** | Docker, Redis |

---

## 🚀 Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis
- Azure OpenAI API access

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gtm_job_intelligence_platform.git
cd gtm_job_intelligence_platform

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_API_KEY="your-key"
export DATABASE_URL="postgresql://user:pass@localhost:5432/gtm_intel"

# Run database migrations
psql -f database/schema.sql

# Start the API
uvicorn api.main:app --reload --port 8000
```

### Running the Scraper

```bash
# Start Redis
redis-server

# Start workers (in separate terminal)
python -m scraper.run

# Enqueue companies to scrape
python -m scraper.enqueue
```

---

## 🔬 Technical Deep-Dive

### ❓ How do you handle 50,000+ requests without getting banned?

Scraping at scale requires a multi-layered anti-detection strategy:

#### 1. **Residential Proxy Rotation**
```python
# Pool of residential proxies rotated per request
def get_proxy():
    proxy = random.choice(PROXY_POOL)
    return {"http": proxy_url, "https": proxy_url}
```
Residential proxies are essential — datacenter IPs get blocked immediately. Each request exits from a different IP address, making it appear as organic traffic from different users.

#### 2. **User-Agent Randomization**
```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0",
    # ... more browser/OS combinations
]
```
Each request appears to come from a different browser and operating system.

#### 3. **Complete Request Headers**
```python
headers = {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "application/json, text/html",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}
```
Full browser-like headers prevent fingerprinting and detection.

#### 4. **Exponential Backoff with Jitter**
```python
BASE_BACKOFF = 1.5
MAX_RETRIES = 5

for attempt in range(MAX_RETRIES):
    response = requests.get(url, proxies=get_proxy())
    if response.status_code == 429:  # Rate limited
        delay = BASE_BACKOFF ** attempt + random.random()
        time.sleep(delay)  # 1.5s → 2.25s → 3.4s → 5.1s → 7.6s
```
Progressive delays with random jitter prevent synchronized retry storms and respect rate limits.

#### 5. **Distributed Workers via Redis Queue**
```python
# 50 concurrent workers, each with own proxy rotation
workers = [Worker(queue, connection=redis_conn) for _ in range(50)]
```
Work is distributed across 50 parallel workers. If one IP gets blocked, others continue unaffected.

#### 6. **API-First Approach (The Secret Weapon)**
Instead of scraping HTML, we hit official ATS APIs:
```
boards-api.greenhouse.io/v1/boards/{company}/jobs
api.lever.co/v0/postings/{company}
api.ashbyhq.com/posting-api/job-board/{company}
api.smartrecruiters.com/v1/companies/{company}/postings
```
APIs are public, more stable, and far less likely to block requests than HTML scraping.

---

### 💰 How much did this cost in LLM tokens?

**Total Cost: ~$45 USD** for processing 14,592 jobs with GPT-4o

#### Token Breakdown

| Component | Tokens | Cost |
|-----------|--------|------|
| **Input** (job descriptions, ~800 tokens avg) | ~11.7M tokens | ~$29 |
| **Output** (structured JSON, ~300 tokens avg) | ~4.4M tokens | ~$13 |
| **System Prompts** (repeated per batch) | ~0.5M tokens | ~$1 |
| **NL Search Queries** (ongoing usage) | Variable | ~$2 |

#### Per-Job Cost
```
$45 ÷ 14,592 jobs = $0.003 per job (0.3 cents)
```

#### Cost Optimization Strategies
1. **Batching** — 20 jobs per API call reduces system prompt overhead
2. **Structured JSON Mode** — Reduces output token waste
3. **Concise Prompts** — Minimal instructions, maximum extraction
4. **PostgreSQL Caching** — Extracted data stored permanently, never re-processed

---

### 📈 How would you scale this to 1 Million jobs?

Scaling 70x (14.5k → 1M jobs) requires architectural changes across every layer:

#### 1. **Database: Horizontal Scaling**

```
Current: Single PostgreSQL instance
At 1M scale:
├── PostgreSQL with Read Replicas (1 writer, 4 readers)
├── Table Partitioning by company or scrape_date
├── Or: CockroachDB / CitusDB for true horizontal sharding
└── Connection pooling with PgBouncer
```

#### 2. **Search: Add Elasticsearch**

```
PostgreSQL ILIKE queries → Elasticsearch

Benefits at scale:
• Full-text search with relevance scoring
• Faceted search (instant filter counts)  
• Sub-100ms queries on 1M+ documents
• Built-in clustering and replication
```

#### 3. **Proxy Infrastructure: 10x Scale**

```
Current: 10 residential proxies
At 1M scale: 100+ proxies via:
├── Bright Data / Oxylabs residential pools
├── Rotating datacenter proxies for stable APIs
├── Geographic distribution (US, EU, APAC regions)
└── Automatic failover and health checks
```

#### 4. **Worker Architecture: Kubernetes**

```yaml
# Current: 50 local Python workers
# At scale: Kubernetes with horizontal pod autoscaling

apiVersion: apps/v1
kind: Deployment
metadata:
  name: scraper-workers
spec:
  replicas: 200  # Scale to 200+ workers
  template:
    spec:
      containers:
      - name: scraper
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 50
  maxReplicas: 500
  metrics:
  - type: Resource
    resource:
      name: cpu
      targetAverageUtilization: 70
```

#### 5. **LLM Processing: Parallel + Smart Caching**

```python
# Optimizations for 1M jobs:

# 1. Larger batches
BATCH_SIZE = 50  # Up from 20

# 2. Parallel API calls
async def process_batch(jobs):
    tasks = [call_openai(batch) for batch in chunks(jobs, 50)]
    return await asyncio.gather(*tasks, max_concurrency=10)

# 3. Semantic deduplication
# Skip nearly-identical job descriptions (saves ~20% tokens)
if embedding_similarity(new_job, cached_job) > 0.95:
    return cached_extraction

# Estimated cost at 1M jobs: ~$3,000-3,500 USD
```

#### 6. **Queue: Redis → Redis Cluster**

```
Single Redis instance → Redis Cluster (6+ nodes)
├── Handles 100k+ jobs in queue
├── Automatic failover
├── Horizontal scaling for throughput
└── Separate queues per priority/ATS
```

#### 7. **API Layer: Caching & CDN**

```
Request Flow at Scale:

User → CloudFlare CDN → Load Balancer → FastAPI Cluster
                              ↓
                        Redis Cache (5 min TTL)
                              ↓
                        PostgreSQL / Elasticsearch
```

#### Estimated Costs at 1M Jobs

| Component | Monthly Cost |
|-----------|-------------|
| Proxy Infrastructure (100+ IPs) | $500 - $1,000 |
| Kubernetes Cluster (AWS/GCP) | $300 - $600 |
| PostgreSQL (RDS/Cloud SQL) | $150 - $300 |
| Elasticsearch (3-node cluster) | $250 - $400 |
| Redis Cluster | $100 - $200 |
| LLM Processing (one-time) | $3,000 - $3,500 |
| **Total First Month** | **~$4,500 - $6,000** |
| **Ongoing Monthly (updates only)** | **~$800 - $1,500** |

#### The Bottom Line

Scaling to 1M jobs is absolutely feasible. The architecture becomes more distributed, but each component has a clear scaling path. The biggest investments are:

1. **Proxy infrastructure** — More IPs = more parallel scraping
2. **LLM costs** — One-time ~$3k investment, then incremental updates
3. **Search infrastructure** — Elasticsearch becomes essential at this scale

With proper caching and incremental updates (only scraping new/changed jobs), ongoing costs stay reasonable at ~$1k/month.

---

## 📁 Project Structure

```
gtm_job_intelligence_platform/
├── api/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration & environment variables
│   ├── db.py                # Database queries, connection pooling
│   ├── static/
│   │   └── index.html       # Frontend SPA
│   └── routes/
│       ├── jobs.py          # Job search & filter endpoints
│       ├── companies.py     # Company browser endpoints
│       └── search.py        # NL search & resume matching
│
├── scraper/
│   ├── config.py            # Proxy pool & ATS API configuration
│   ├── scraper.py           # Core scraping logic
│   ├── companies.py         # Company registry (144 companies)
│   ├── enqueue.py           # Queue job dispatcher
│   └── run.py               # Worker process runner
│
├── worker/
│   ├── extractor.py         # LLM-powered field extraction
│   ├── normalizer.py        # Data cleaning & normalization
│   └── tasks.py             # Async task definitions
│
├── database/
│   ├── schema.sql           # PostgreSQL table definitions
│   ├── loader.py            # Batch data loading utilities
│   └── query.py             # Query builder helpers
│
├── data/
│   ├── scraped/             # Raw JSON from ATS APIs
│   │   ├── greenhouse/
│   │   ├── lever/
│   │   ├── ashby/
│   │   └── smartrecruiters/
│   ├── extracted/           # LLM-processed structured data
│   └── profiles/            # Company metadata
│
└── docs/
    └── screenshots/         # Demo images for README
```

---

## 🔮 Future Improvements

- [ ] **Enhanced Salary Extraction** — Scrape `compensationTierSummary` from Ashby HTML pages
- [ ] **Scheduled Scraping** — Daily/weekly automated job refresh via cron
- [ ] **User Authentication** — Save searches, bookmark jobs, track applications
- [ ] **Email Alerts** — Get notified when new jobs match your criteria
- [ ] **Export Functionality** — Download search results as CSV/Excel
- [ ] **Analytics Dashboard** — Hiring trends, salary insights, tech stack popularity
- [ ] **Browser Extension** — Match jobs while browsing LinkedIn/company sites

---

## 📄 License

MIT License — feel free to use for personal or commercial projects.

---

## 🙏 Acknowledgments

- **Azure OpenAI** for GPT-4o powering intelligent extraction and search
- **Greenhouse, Lever, Ashby, SmartRecruiters** for providing public job APIs
- **The Python ecosystem** for excellent scraping, web framework, and data processing libraries

---

<div align="center">

**Built with ☕ and curiosity**

*If you found this useful, consider giving it a ⭐*

</div>
