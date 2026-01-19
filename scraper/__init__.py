"""
Main Scraper Package
Clean, organized scraper that extracts job descriptions directly from ATS APIs.
"""

from .scraper import scrape_company, scrape_and_save
from .tasks import scrape_company_task
from .config import OUTPUT_DIR, REGISTRY_FILE

__all__ = [
    "scrape_company",
    "scrape_and_save", 
    "scrape_company_task",
    "OUTPUT_DIR",
    "REGISTRY_FILE",
]
