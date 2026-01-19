"""Skill and tech stack normalization for consistency across 50k+ jobs."""

from typing import List, Set

# Canonical skill mappings (variant -> canonical form)
TECH_STACK_MAPPINGS = {
    # JavaScript ecosystem
    "js": "javascript",
    "node": "nodejs",
    "node.js": "nodejs",
    "nodjs": "nodejs",
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "angular.js": "angular",
    "angularjs": "angular",
    "next.js": "nextjs",
    "nuxt.js": "nuxtjs",
    "express.js": "express",
    "expressjs": "express",
    "nest.js": "nestjs",
    "nestjs": "nestjs",
    "typescript": "typescript",
    "ts": "typescript",
    
    # Python ecosystem
    "python3": "python",
    "py": "python",
    "django rest framework": "django",
    "drf": "django",
    "fast api": "fastapi",
    "flask": "flask",
    "pytorch": "pytorch",
    "torch": "pytorch",
    "tensor flow": "tensorflow",
    "tf": "tensorflow",
    "scikit-learn": "sklearn",
    "scikit learn": "sklearn",
    "sci-kit learn": "sklearn",
    "pandas": "pandas",
    "numpy": "numpy",
    
    # Databases
    "postgres": "postgresql",
    "psql": "postgresql",
    "mongo": "mongodb",
    "mongo db": "mongodb",
    "mysql": "mysql",
    "maria db": "mariadb",
    "mariadb": "mariadb",
    "redis": "redis",
    "elastic search": "elasticsearch",
    "elastic": "elasticsearch",
    "dynamodb": "dynamodb",
    "dynamo db": "dynamodb",
    "cassandra": "cassandra",
    "cockroach db": "cockroachdb",
    "cockroachdb": "cockroachdb",
    
    # Cloud providers
    "amazon web services": "aws",
    "amazon aws": "aws",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "azure": "azure",
    "microsoft azure": "azure",
    
    # DevOps/Infra
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "docker": "docker",
    "terraform": "terraform",
    "ansible": "ansible",
    "jenkins": "jenkins",
    "github actions": "github-actions",
    "gitlab ci": "gitlab-ci",
    "circle ci": "circleci",
    "circleci": "circleci",
    
    # Data tools
    "apache spark": "spark",
    "pyspark": "spark",
    "apache kafka": "kafka",
    "apache airflow": "airflow",
    "apache flink": "flink",
    "snowflake": "snowflake",
    "databricks": "databricks",
    "dbt": "dbt",
    "data build tool": "dbt",
    "looker": "looker",
    "tableau": "tableau",
    "power bi": "powerbi",
    "powerbi": "powerbi",
    
    # Languages
    "golang": "go",
    "c++": "cpp",
    "c plus plus": "cpp",
    "c#": "csharp",
    "c sharp": "csharp",
    ".net": "dotnet",
    "dotnet": "dotnet",
    "rust": "rust",
    "scala": "scala",
    "kotlin": "kotlin",
    "swift": "swift",
    "objective-c": "objective-c",
    "ruby on rails": "rails",
    "ror": "rails",
    
    # AI/ML
    "machine learning": "ml",
    "deep learning": "deep-learning",
    "natural language processing": "nlp",
    "computer vision": "cv",
    "large language models": "llm",
    "llms": "llm",
    "generative ai": "genai",
    "gen ai": "genai",
    "openai": "openai",
    "langchain": "langchain",
    "hugging face": "huggingface",
    "huggingface": "huggingface",
}

SKILL_MAPPINGS = {
    # Soft skills
    "communication skills": "communication",
    "written communication": "communication",
    "verbal communication": "communication",
    "problem solving": "problem-solving",
    "problem-solving skills": "problem-solving",
    "critical thinking": "critical-thinking",
    "team work": "teamwork",
    "team player": "teamwork",
    "cross-functional collaboration": "cross-functional",
    "cross functional": "cross-functional",
    "leadership skills": "leadership",
    "project management": "project-management",
    "time management": "time-management",
    "attention to detail": "detail-oriented",
    
    # Technical skills
    "rest api": "rest-apis",
    "restful api": "rest-apis",
    "restful apis": "rest-apis",
    "api design": "api-design",
    "microservices architecture": "microservices",
    "distributed systems": "distributed-systems",
    "system design": "system-design",
    "data structures": "data-structures",
    "algorithms": "algorithms",
    "data structures and algorithms": "dsa",
    "dsa": "dsa",
    "object oriented programming": "oop",
    "object-oriented programming": "oop",
    "oop": "oop",
    "functional programming": "functional-programming",
    "test driven development": "tdd",
    "test-driven development": "tdd",
    "tdd": "tdd",
    "continuous integration": "ci-cd",
    "continuous deployment": "ci-cd",
    "ci/cd": "ci-cd",
    "cicd": "ci-cd",
    "agile methodology": "agile",
    "agile development": "agile",
    "scrum": "scrum",
    "kanban": "kanban",
    
    # Domain expertise
    "machine learning": "machine-learning",
    "data analysis": "data-analysis",
    "data analytics": "data-analysis",
    "business intelligence": "bi",
    "bi": "bi",
    "data modeling": "data-modeling",
    "data engineering": "data-engineering",
    "data science": "data-science",
    "devops": "devops",
    "dev ops": "devops",
    "site reliability engineering": "sre",
    "sre": "sre",
    "security": "security",
    "cybersecurity": "cybersecurity",
    "cloud computing": "cloud",
    "cloud infrastructure": "cloud",
}


def normalize_term(term: str, mappings: dict) -> str:
    """Normalize a single term using the mapping dictionary."""
    if not term:
        return ""
    
    # Clean and lowercase
    cleaned = term.lower().strip()
    
    # Look up in mappings
    if cleaned in mappings:
        return mappings[cleaned]
    
    return cleaned


def normalize_tech_stack(tech_list: List[str]) -> List[str]:
    """
    Normalize tech stack to canonical forms.
    
    Example:
        ["Node", "node.js", "NodeJS"] -> ["nodejs"]
        ["k8s", "Kubernetes"] -> ["kubernetes"]
    """
    if not tech_list:
        return []
    
    normalized: Set[str] = set()
    
    for tech in tech_list:
        norm = normalize_term(tech, TECH_STACK_MAPPINGS)
        if norm:
            normalized.add(norm)
    
    return sorted(list(normalized))


def normalize_skills(skill_list: List[str]) -> List[str]:
    """
    Normalize skills to canonical forms.
    
    Example:
        ["Problem Solving", "problem-solving skills"] -> ["problem-solving"]
    """
    if not skill_list:
        return []
    
    normalized: Set[str] = set()
    
    for skill in skill_list:
        norm = normalize_term(skill, SKILL_MAPPINGS)
        if norm:
            normalized.add(norm)
    
    return sorted(list(normalized))


def get_all_canonical_terms() -> dict:
    """Return all canonical terms for reference."""
    return {
        "tech_stack": sorted(set(TECH_STACK_MAPPINGS.values())),
        "skills": sorted(set(SKILL_MAPPINGS.values()))
    }
