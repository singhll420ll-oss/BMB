"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db
from core.security import create_access_token, verify_password
from crud import user, user_session
from schemas.user import UserCreate, UserLogin
from models.user import UserRole
from core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, role: Optional[str] = "customer"):
    """Login page"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "role": role}
    )

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle login form submission"""
    # Authenticate user
    db_user = await user.authenticate(db, username, password)
    
    if not db_user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "role": role,
                "error": "Invalid username or password"
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check role
    if db_user.role != role:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "role": role,
                "error": f"User is not a {role.replace('_', ' ')}"
            },
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Create session record
    session = await user_session.create_login(db, db_user.id)
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": db_user.username,
            "user_id": db_user.id,
            "role": db_user.role
        }
    )
    
    # Set cookie
    response = RedirectResponse(
        url="/customer/dashboard" if db_user.role == UserRole.CUSTOMER else
            "/team/dashboard" if db_user.role == UserRole.TEAM_MEMBER else
            "/admin/dashboard",
        status_code=status.HTTP_302_FOUND
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    # Store session ID in cookie
    response.set_cookie(
        key="session_id",
        value=str(session.id),
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )

@router.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    address: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle registration form submission"""
    # Check if passwords match
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Passwords do not match"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if username exists
    existing_user = await user.get_by_username(db, username)
    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Username already exists"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if email exists
    existing_email = await user.get_by_email(db, email)
    if existing_email:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Email already registered"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user
    user_data = UserCreate(
        name=name,
        username=username,
        email=email,
        phone=phone,
        password=password,
        address=address,
        role=UserRole.CUSTOMER
    )
    
    try:
        db_user = await user.create(db, user_data)
        
        # Create session record
        session = await user_session.create_login(db, db_user.id)
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": db_user.username,
                "user_id": db_user.id,
                "role": db_user.role
            }
        )
        
        # Set cookie and redirect
        response = RedirectResponse(
            url="/customer/dashboard",
            status_code=status.HTTP_302_FOUND
        )
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=not settings.DEBUG,
            samesite="lax"
        )
        
        response.set_cookie(
            key="session_id",
            value=str(session.id),
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=not settings.DEBUG,
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": f"Registration failed: {str(e)}"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle logout"""
    # Get session ID from cookie
    session_id = request.cookies.get("session_id")
    
    if session_id:
        try:
            await user_session.update_logout(db, int(session_id))
        except:
            pass
    
    # Clear cookies
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    response.delete_cookie("session_id")
    
    return response

@router.get("/admin-login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page (accessed via secret clock)"""
    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request}
    )

@router.post("/admin-login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle admin login"""
    # Authenticate admin
    db_user = await user.authenticate(db, username, password)
    
    if not db_user:
        return templates.TemplateResponse(
            "admin_login.html",
            {
                "request": request,
                "error": "Invalid username or password"
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if user is admin
    if db_user.role != UserRole.ADMIN:
        return templates.TemplateResponse(
            "admin_login.html",
            {
                "request": request,
                "error": "Access denied. Admin privileges required."
            },
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Create session record
    session = await user_session.create_login(db, db_user.id)
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": db_user.username,
            "user_id": db_user.id,
            "role": db_user.role
        }
    )
    
    # Set cookie and redirect
    response = RedirectResponse(
        url="/admin/dashboard",
        status_code=status.HTTP_302_FOUND
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    response.set_cookie(
        key="session_id",
        value=str(session.id),
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    return response
