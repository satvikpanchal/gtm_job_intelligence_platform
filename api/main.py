"""FastAPI application for GTM Intelligence Platform."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

from .routes import jobs, companies, search
from .config import DEBUG

# Create FastAPI app
app = FastAPI(
    title="GTM Job Intelligence API",
    description="Search and analyze 50k+ job postings for Go-To-Market intelligence",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])

# Serve static files (UI)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path) as f:
            return f.read()
    return """
    <html>
        <head><title>GTM Intelligence</title></head>
        <body>
            <h1>GTM Job Intelligence API</h1>
            <p>API Documentation: <a href="/api/docs">/api/docs</a></p>
        </body>
    </html>
    """


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/stats")
async def stats():
    """Get platform statistics."""
    from .db import get_stats
    return get_stats()
