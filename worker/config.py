"""Worker configuration for distributed processing."""

import os

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Queue names
SCRAPE_QUEUE = "scrape"
EXTRACT_QUEUE = "extract"

# Ollama configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")  # Faster model
OLLAMA_TIMEOUT = 120  # Increased timeout for parallel requests

# Worker settings
BURST_MODE = True  # Workers exit when queue empty (macOS-safe)
MAX_RETRIES = 3

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRAPED_DIR = os.path.join(BASE_DIR, "data", "scraped")
EXTRACTED_DIR = os.path.join(BASE_DIR, "data", "extracted")
PROFILES_DIR = os.path.join(BASE_DIR, "data", "profiles")

# Create directories
for d in [SCRAPED_DIR, EXTRACTED_DIR, PROFILES_DIR]:
    os.makedirs(d, exist_ok=True)
