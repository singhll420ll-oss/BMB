"""
Public routes (no authentication required)
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["public"])
templates = Jinja2Templates(directory="templates")

@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About page"""
    return templates.TemplateResponse(
        "about.html",
        {"request": request}
    )

@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """Contact page"""
    return templates.TemplateResponse(
        "contact.html",
        {"request": request}
    )

@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """Privacy policy page"""
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request}
    )

@router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    """Terms of service page"""
    return templates.TemplateResponse(
        "terms.html",
        {"request": request}
    )
