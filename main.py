"""
Bite Me Buddy - Food Ordering System
Main FastAPI application entry point
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from core.config import settings
from core.logger import setup_logging
from database import engine, Base
from routers import auth, customer, team_member, admin, public
from core.utils import create_upload_dirs

# Setup structured logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    logger.info("Starting Bite Me Buddy application")
    
    # Create upload directories if they don't exist
    create_upload_dirs()
    
    # Create database tables (in production, use Alembic migrations)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Bite Me Buddy application")
    await engine.dispose()

# Create FastAPI app
app = FastAPI(
    title="Bite Me Buddy Food Ordering",
    description="Production-ready food ordering system with admin, team member, and customer portals",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router, tags=["authentication"])
app.include_router(customer.router, tags=["customer"])
app.include_router(team_member.router, tags=["team_member"])
app.include_router(admin.router, tags=["admin"])
app.include_router(public.router, tags=["public"])

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Home page with clock and three buttons"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    """Custom 404 handler"""
    return templates.TemplateResponse(
        "404.html", 
        {"request": request},
        status_code=404
    )

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc):
    """Custom 500 handler"""
    logger.error(f"Server error: {exc}")
    return templates.TemplateResponse(
        "500.html",
        {"request": request},
        status_code=500
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )