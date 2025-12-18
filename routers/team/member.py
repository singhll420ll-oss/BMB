"""
Team Member routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from database import get_db
from core.security import get_current_user
from crud import order, team_member_plan, user
from models.user import UserRole
from core.utils import send_sms_via_twilio

router = APIRouter(prefix="/team", tags=["team_member"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def team_member_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.TEAM_MEMBER])),
    db: AsyncSession = Depends(get_db)
):
    """Team member dashboard"""
    # Get assigned orders
    assigned_orders = await order.get_by_team_member(db, current_user["user_id"])
    
    # Get today's plans
    today_plans = await team_member_plan.get_by_team_member(db, current_user["user_id"])
    
    # Get user info
    db_user = await user.get_by_id(db, current_user["user_id"])
    
    return templates.TemplateResponse(
        "team_member_dashboard.html",
        {
            "request": request,
            "user": current_user,
            "db_user": db_user,
            "assigned_orders": assigned_orders,
            "today_plans": today_plans
        }
    )

@router.post("/order/{order_id}/request-otp")
async def request_otp(
    request: Request,
    order_id: int,
    current_user: dict = Depends(get_current_user([UserRole.TEAM_MEMBER])),
    db: AsyncSession = Depends(get_db)
):
    """Request OTP for order delivery"""
    # Get order
    db_order = await order.get_by_id(db, order_id)
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order is assigned to this team member
    if db_order.assigned_to != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Order not assigned to you")
    
    # Check if order is out for delivery
    if db_order.status != "out_for_delivery":
        raise HTTPException(status_code=400, detail="Order is not out for delivery")
    
    # Generate OTP
    otp, otp_expiry = await order.generate_otp(db, order_id)
    
    # Get customer phone
    customer_phone = db_order.customer.phone
    
    # Send SMS via Twilio
    message = f"Bite Me Buddy Delivery OTP: {otp}. Valid for 5 minutes. Order ID: {order_id}"
    
    try:
        await send_sms_via_twilio(customer_phone, message)
    except Exception as e:
        # Log error but continue (OTP is still generated)
        print(f"Failed to send SMS: {e}")
    
    # Return HTML snippet for HTMX
    return HTMLResponse(f"""
    <div class="alert alert-success" role="alert">
        OTP sent to customer. OTP will expire at {otp_expiry.strftime('%H:%M:%S')}
    </div>
    <form hx-post="/team/order/{order_id}/verify-otp" hx-target="#otp-section-{order_id}">
        <div class="mb-3">
            <label for="otp" class="form-label">Enter OTP</label>
            <input type="text" class="form-control" id="otp" name="otp" 
                   placeholder="4-digit OTP" pattern="\\d{{4}}" required>
        </div>
        <button type="submit" class="btn btn-success">
            <i class="fas fa-check-circle"></i> Verify OTP & Complete Delivery
        </button>
    </form>
    """)

@router.post("/order/{order_id}/verify-otp")
async def verify_otp(
    request: Request,
    order_id: int,
    otp: str = Form(...),
    current_user: dict = Depends(get_current_user([UserRole.TEAM_MEMBER])),
    db: AsyncSession = Depends(get_db)
):
    """Verify OTP and complete delivery"""
    # Get order
    db_order = await order.get_by_id(db, order_id)
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order is assigned to this team member
    if db_order.assigned_to != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Order not assigned to you")
    
    # Verify OTP
    is_valid = await order.verify_otp(db, order_id, otp)
    
    if not is_valid:
        return HTMLResponse(f"""
        <div class="alert alert-danger" role="alert">
            Invalid or expired OTP. Please request a new one.
        </div>
        <button class="btn btn-primary" 
                hx-post="/team/order/{order_id}/request-otp"
                hx-target="#otp-section-{order_id}">
            <i class="fas fa-redo"></i> Request New OTP
        </button>
        """)
    
    # Update order status
    from schemas.order import OrderUpdate
    
    order_update = OrderUpdate(
        status="delivered",
        delivery_confirmed_at=datetime.utcnow()
    )
    
    await order.update(db, order_id, order_update)
    
    # Return success message
    return HTMLResponse(f"""
    <div class="alert alert-success" role="alert">
        <i class="fas fa-check-circle"></i> Delivery confirmed successfully!
    </div>
    <div class="d-grid">
        <button class="btn btn-success" disabled>
            <i class="fas fa-check"></i> Delivered
        </button>
    </div>
    """)

@router.get("/orders", response_class=HTMLResponse)
async def team_orders(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.TEAM_MEMBER])),
    db: AsyncSession = Depends(get_db)
):
    """Team member's assigned orders"""
    orders = await order.get_by_team_member(db, current_user["user_id"])
    return templates.TemplateResponse(
        "team_orders.html",
        {
            "request": request,
            "user": current_user,
            "orders": orders
        }
    )

@router.get("/plans", response_class=HTMLResponse)
async def team_plans(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.TEAM_MEMBER])),
    db: AsyncSession = Depends(get_db)
):
    """Team member's plans"""
    plans = await team_member_plan.get_by_team_member(db, current_user["user_id"])
    return templates.TemplateResponse(
        "team_plans.html",
        {
            "request": request,
            "user": current_user,
            "plans": plans
        }
    )
