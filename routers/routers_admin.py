"""
Admin routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os
from pathlib import Path

from database import get_db
from core.security import get_current_user
from crud import user, service, menu_item, order, team_member_plan, user_session
from schemas.user import UserCreate, UserUpdate
from schemas.service import ServiceCreate, ServiceUpdate
from schemas.menu_item import MenuItemCreate, MenuItemUpdate
from schemas.team_member_plan import TeamMemberPlanCreate
from models.user import UserRole
from core.utils import save_uploaded_file, delete_file

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Admin dashboard"""
    # Get statistics
    order_stats = await order.get_stats(db)
    user_stats = {
        "total_customers": len(await user.get_by_role(db, UserRole.CUSTOMER)),
        "total_team_members": len(await user.get_by_role(db, UserRole.TEAM_MEMBER)),
        "total_admins": len(await user.get_by_role(db, UserRole.ADMIN))
    }
    
    # Get recent orders
    recent_orders = await order.get_all(db, limit=10)
    
    # Get active sessions
    active_sessions = await user_session.get_active_sessions(db)
    
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "user": current_user,
            "order_stats": order_stats,
            "user_stats": user_stats,
            "recent_orders": recent_orders,
            "active_sessions": active_sessions
        }
    )

# Services Management
@router.get("/services", response_class=HTMLResponse)
async def manage_services(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Manage services page"""
    services = await service.get_all(db)
    return templates.TemplateResponse(
        "manage_services.html",
        {
            "request": request,
            "user": current_user,
            "services": services
        }
    )

@router.post("/services")
async def create_service(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Create new service"""
    image_url = None
    if image and image.filename:
        image_url = await save_uploaded_file(image, "services")
    
    service_data = ServiceCreate(
        name=name,
        description=description,
        image_url=image_url
    )
    
    db_service = await service.create(db, service_data)
    
    # Return HTML snippet for HTMX
    return HTMLResponse(f"""
    <tr id="service-{db_service.id}">
        <td>{db_service.id}</td>
        <td>
            {f'<img src="{db_service.image_url}" alt="{db_service.name}" class="service-img">' if db_service.image_url else ''}
            {db_service.name}
        </td>
        <td>{db_service.description or '-'}</td>
        <td>
            <a href="/admin/service/{db_service.id}/menu" class="btn btn-sm btn-info">
                <i class="fas fa-utensils"></i> Menu
            </a>
            <button class="btn btn-sm btn-warning" 
                    hx-get="/admin/services/{db_service.id}/edit"
                    hx-target="#service-{db_service.id}"
                    hx-swap="outerHTML">
                <i class="fas fa-edit"></i> Edit
            </button>
            <button class="btn btn-sm btn-danger"
                    hx-delete="/admin/services/{db_service.id}"
                    hx-confirm="Are you sure you want to delete this service?"
                    hx-target="#service-{db_service.id}"
                    hx-swap="outerHTML">
                <i class="fas fa-trash"></i> Delete
            </button>
        </td>
    </tr>
    """)

@router.get("/services/{service_id}/edit")
async def edit_service_form(
    request: Request,
    service_id: int,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get edit service form"""
    db_service = await service.get_by_id(db, service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return HTMLResponse(f"""
    <tr id="service-{db_service.id}">
        <td>{db_service.id}</td>
        <td colspan="2">
            <form hx-post="/admin/services/{service_id}" 
                  hx-target="#service-{service_id}"
                  hx-encoding="multipart/form-data">
                <div class="row g-2">
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="name" 
                               value="{db_service.name}" required>
                    </div>
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="description" 
                               value="{db_service.description or ''}">
                    </div>
                    <div class="col-md-4">
                        <input type="file" class="form-control" name="image" accept="image/*">
                    </div>
                </div>
                <div class="mt-2">
                    <button type="submit" class="btn btn-sm btn-success">
                        <i class="fas fa-save"></i> Save
                    </button>
                    <button type="button" class="btn btn-sm btn-secondary"
                            hx-get="/admin/services/{service_id}"
                            hx-target="#service-{service_id}">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </div>
            </form>
        </td>
        <td></td>
    </tr>
    """)

@router.post("/services/{service_id}")
async def update_service(
    request: Request,
    service_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Update service"""
    db_service = await service.get_by_id(db, service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    image_url = db_service.image_url
    if image and image.filename:
        # Delete old image if exists
        if db_service.image_url:
            await delete_file(db_service.image_url)
        image_url = await save_uploaded_file(image, "services")
    
    service_data = ServiceUpdate(
        name=name,
        description=description,
        image_url=image_url
    )
    
    updated_service = await service.update(db, service_id, service_data)
    
    # Return updated row
    return HTMLResponse(f"""
    <tr id="service-{updated_service.id}">
        <td>{updated_service.id}</td>
        <td>
            {f'<img src="{updated_service.image_url}" alt="{updated_service.name}" class="service-img">' if updated_service.image_url else ''}
            {updated_service.name}
        </td>
        <td>{updated_service.description or '-'}</td>
        <td>
            <a href="/admin/service/{updated_service.id}/menu" class="btn btn-sm btn-info">
                <i class="fas fa-utensils"></i> Menu
            </a>
            <button class="btn btn-sm btn-warning" 
                    hx-get="/admin/services/{updated_service.id}/edit"
                    hx-target="#service-{updated_service.id}"
                    hx-swap="outerHTML">
                <i class="fas fa-edit"></i> Edit
            </button>
            <button class="btn btn-sm btn-danger"
                    hx-delete="/admin/services/{updated_service.id}"
                    hx-confirm="Are you sure you want to delete this service?"
                    hx-target="#service-{updated_service.id}"
                    hx-swap="outerHTML">
                <i class="fas fa-trash"></i> Delete
            </button>
        </td>
    </tr>
    """)

@router.delete("/services/{service_id}")
async def delete_service(
    request: Request,
    service_id: int,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Delete service"""
    db_service = await service.get_by_id(db, service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Delete image if exists
    if db_service.image_url:
        await delete_file(db_service.image_url)
    
    # Delete service
    await service.delete(db, service_id)
    
    # Return empty response (row will be removed)
    return HTMLResponse("")

# Menu Items Management
@router.get("/service/{service_id}/menu", response_class=HTMLResponse)
async def manage_menu(
    request: Request,
    service_id: int,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Manage menu items for a service"""
    db_service = await service.get_by_id(db, service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    menu_items = await menu_item.get_by_service(db, service_id)
    
    return templates.TemplateResponse(
        "manage_menu.html",
        {
            "request": request,
            "user": current_user,
            "service": db_service,
            "menu_items": menu_items
        }
    )

@router.post("/service/{service_id}/menu")
async def create_menu_item(
    request: Request,
    service_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Create new menu item"""
    image_url = None
    if image and image.filename:
        image_url = await save_uploaded_file(image, "menu")
    
    menu_item_data = MenuItemCreate(
        service_id=service_id,
        name=name,
        description=description,
        price=price,
        image_url=image_url
    )
    
    db_menu_item = await menu_item.create(db, menu_item_data)
    
    # Return HTML snippet for HTMX
    return HTMLResponse(f"""
    <tr id="menu-item-{db_menu_item.id}">
        <td>{db_menu_item.id}</td>
        <td>
            {f'<img src="{db_menu_item.image_url}" alt="{db_menu_item.name}" class="menu-item-img">' if db_menu_item.image_url else ''}
            {db_menu_item.name}
        </td>
        <td>{db_menu_item.description or '-'}</td>
        <td>₹{db_menu_item.price:.2f}</td>
        <td>
            <button class="btn btn-sm btn-warning" 
                    hx-get="/admin/menu/{db_menu_item.id}/edit"
                    hx-target="#menu-item-{db_menu_item.id}"
                    hx-swap="outerHTML">
                <i class="fas fa-edit"></i> Edit
            </button>
            <button class="btn btn-sm btn-danger"
                    hx-delete="/admin/menu/{db_menu_item.id}"
                    hx-confirm="Are you sure you want to delete this menu item?"
                    hx-target="#menu-item-{db_menu_item.id}"
                    hx-swap="outerHTML">
                <i class="fas fa-trash"></i> Delete
            </button>
        </td>
    </tr>
    """)

@router.get("/menu/{menu_item_id}/edit")
async def edit_menu_item_form(
    request: Request,
    menu_item_id: int,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get edit menu item form"""
    db_menu_item = await menu_item.get_by_id(db, menu_item_id)
    if not db_menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    return HTMLResponse(f"""
    <tr id="menu-item-{db_menu_item.id}">
        <td>{db_menu_item.id}</td>
        <td colspan="3">
            <form hx-post="/admin/menu/{menu_item_id}" 
                  hx-target="#menu-item-{menu_item_id}"
                  hx-encoding="multipart/form-data">
                <div class="row g-2">
                    <div class="col-md-3">
                        <input type="text" class="form-control" name="name" 
                               value="{db_menu_item.name}" required>
                    </div>
                    <div class="col-md-3">
                        <input type="text" class="form-control" name="description" 
                               value="{db_menu_item.description or ''}">
                    </div>
                    <div class="col-md-2">
                        <input type="number" class="form-control" name="price" 
                               value="{db_menu_item.price}" step="0.01" min="0" required>
                    </div>
                    <div class="col-md-4">
                        <input type="file" class="form-control" name="image" accept="image/*">
                    </div>
                </div>
                <div class="mt-2">
                    <button type="submit" class="btn btn-sm btn-success">
                        <i class="fas fa-save"></i> Save
                    </button>
                    <button type="button" class="btn btn-sm btn-secondary"
                            hx-get="/admin/menu/{menu_item_id}"
                            hx-target="#menu-item-{menu_item_id}">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </div>
            </form>
        </td>
        <td></td>
    </tr>
    """)

@router.post("/menu/{menu_item_id}")
async def update_menu_item(
    request: Request,
    menu_item_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Update menu item"""
    db_menu_item = await menu_item.get_by_id(db, menu_item_id)
    if not db_menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    image_url = db_menu_item.image_url
    if image and image.filename:
        # Delete old image if exists
        if db_menu_item.image_url:
            await delete_file(db_menu_item.image_url)
        image_url = await save_uploaded_file(image, "menu")
    
    menu_item_data = MenuItemUpdate(
        name=name,
        description=description,
        price=price,
        image_url=image_url
    )
    
    updated_menu_item = await menu_item.update(db, menu_item_id, menu_item_data)
    
    # Return updated row
    return HTMLResponse(f"""
    <tr id="menu-item-{updated_menu_item.id}">
        <td>{updated_menu_item.id}</td>
        <td>
            {f'<img src="{updated_menu_item.image_url}" alt="{updated_menu_item.name}" class="menu-item-img">' if updated_menu_item.image_url else ''}
            {updated_menu_item.name}
        </td>
        <td>{updated_menu_item.description or '-'}</td>
        <td>₹{updated_menu_item.price:.2f}</td>
        <td>
            <button class="btn btn-sm btn-warning" 
                    hx-get="/admin/menu/{updated_menu_item.id}/edit"
                    hx-target="#menu-item-{updated_menu_item.id}"
                    hx-swap="outerHTML">
                <i class="fas fa-edit"></i> Edit
            </button>
            <button class="btn btn-sm btn-danger"
                    hx-delete="/admin/menu/{updated_menu_item.id}"
                    hx-confirm="Are you sure you want to delete this menu item?"
                    hx-target="#menu-item-{updated_menu_item.id}"
                    hx-swap="outerHTML">
                <i class="fas fa-trash"></i> Delete
            </button>
        </td>
    </tr>
    """)

@router.delete("/menu/{menu_item_id}")
async def delete_menu_item(
    request: Request,
    menu_item_id: int,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Delete menu item"""
    db_menu_item = await menu_item.get_by_id(db, menu_item_id)
    if not db_menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Delete image if exists
    if db_menu_item.image_url:
        await delete_file(db_menu_item.image_url)
    
    # Delete menu item
    await menu_item.delete(db, menu_item_id)
    
    # Return empty response (row will be removed)
    return HTMLResponse("")

# Team Members Management
@router.get("/team-members", response_class=HTMLResponse)
async def manage_team_members(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Manage team members page"""
    team_members = await user.get_by_role(db, UserRole.TEAM_MEMBER)
    return templates.TemplateResponse(
        "manage_team_members.html",
        {
            "request": request,
            "user": current_user,
            "team_members": team_members
        }
    )

@router.post("/team-members")
async def create_team_member(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    address: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Create new team member"""
    # Check if username exists
    existing_user = await user.get_by_username(db, username)
    if existing_user:
        return HTMLResponse(f"""
        <div class="alert alert-danger" role="alert">
            Username already exists
        </div>
        """)
    
    user_data = UserCreate(
        name=name,
        username=username,
        email=email,
        phone=phone,
        password=password,
        address=address,
        role=UserRole.TEAM_MEMBER
    )
    
    db_user = await user.create(db, user_data)
    
    # Return HTML snippet for HTMX
    return HTMLResponse(f"""
    <tr id="team-member-{db_user.id}">
        <td>{db_user.id}</td>
        <td>{db_user.name}</td>
        <td>{db_user.username}</td>
        <td>{db_user.email}</td>
        <td>{db_user.phone}</td>
        <td>
            <button class="btn btn-sm btn-warning" 
                    hx-get="/admin/team-members/{db_user.id}/edit"
                    hx-target="#team-member-{db_user.id}"
                    hx-swap="outerHTML">
                <i class="fas fa-edit"></i> Edit
            </button>
            <button class="btn btn-sm btn-danger"
                    hx-delete="/admin/team-members/{db_user.id}"
                    hx-confirm="Are you sure you want to delete this team member?"
                    hx-target="#team-member-{db_user.id}"
                    hx-swap="outerHTML">
                <i class="fas fa-trash"></i> Delete
            </button>
        </td>
    </tr>
    """)

@router.delete("/team-members/{user_id}")
async def delete_team_member(
    request: Request,
    user_id: int,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Delete team member"""
    db_user = await user.get_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is a team member
    if db_user.role != UserRole.TEAM_MEMBER:
        raise HTTPException(status_code=400, detail="User is not a team member")
    
    # Delete user
    await user.delete(db, user_id)
    
    # Return empty response (row will be removed)
    return HTMLResponse("")

# Orders Management
@router.get("/orders", response_class=HTMLResponse)
async def view_orders(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """View all orders"""
    orders = await order.get_all(db)
    team_members = await user.get_by_role(db, UserRole.TEAM_MEMBER)
    
    return templates.TemplateResponse(
        "view_orders.html",
        {
            "request": request,
            "user": current_user,
            "orders": orders,
            "team_members": team_members
        }
    )

@router.post("/orders/{order_id}/assign")
async def assign_order(
    request: Request,
    order_id: int,
    team_member_id: int = Form(...),
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Assign order to team member"""
    from schemas.order import OrderUpdate
    
    order_update = OrderUpdate(
        assigned_to=team_member_id,
        status="assigned"
    )
    
    updated_order = await order.update(db, order_id, order_update)
    
    # Return updated status
    if updated_order.team_member:
        assigned_to_name = updated_order.team_member.name
    else:
        assigned_to_name = "Unassigned"
    
    return HTMLResponse(f"""
    <span class="badge bg-warning">Assigned to {assigned_to_name}</span>
    <button class="btn btn-sm btn-primary"
            hx-get="/admin/orders/{order_id}/assign-form"
            hx-target="#assign-section-{order_id}">
        <i class="fas fa-edit"></i> Change
    </button>
    """)

@router.get("/orders/{order_id}/assign-form")
async def get_assign_form(
    request: Request,
    order_id: int,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get assign order form"""
    db_order = await order.get_by_id(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    team_members = await user.get_by_role(db, UserRole.TEAM_MEMBER)
    
    options_html = ""
    for tm in team_members:
        selected = "selected" if db_order.assigned_to == tm.id else ""
        options_html += f'<option value="{tm.id}" {selected}>{tm.name}</option>'
    
    return HTMLResponse(f"""
    <form hx-post="/admin/orders/{order_id}/assign" 
          hx-target="#assign-section-{order_id}">
        <div class="input-group input-group-sm">
            <select class="form-select" name="team_member_id" required>
                <option value="">Select Team Member</option>
                {options_html}
            </select>
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-save"></i> Assign
            </button>
            <button type="button" class="btn btn-secondary"
                    hx-get="/admin/orders/{order_id}/assign-status"
                    hx-target="#assign-section-{order_id}">
                Cancel
            </button>
        </div>
    </form>
    """)

# Customers Management
@router.get("/customers", response_class=HTMLResponse)
async def view_customers(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """View all customers"""
    customers = await user.get_by_role(db, UserRole.CUSTOMER)
    return templates.TemplateResponse(
        "view_customers.html",
        {
            "request": request,
            "user": current_user,
            "customers": customers
        }
    )

@router.get("/customer/{customer_id}", response_class=HTMLResponse)
async def customer_detail(
    request: Request,
    customer_id: int,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Customer detail page"""
    db_user = await user.get_by_id(db, customer_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get customer orders
    customer_orders = await order.get_by_customer(db, customer_id)
    
    # Get customer sessions
    customer_sessions = await user_session.get_user_sessions(db, customer_id)
    
    return templates.TemplateResponse(
        "customer_detail.html",
        {
            "request": request,
            "user": current_user,
            "customer": db_user,
            "orders": customer_orders,
            "sessions": customer_sessions
        }
    )

# Plans Management
@router.get("/plans", response_class=HTMLResponse)
async def send_plans(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Send plans to team members"""
    team_members = await user.get_by_role(db, UserRole.TEAM_MEMBER)
    recent_plans = await team_member_plan.get_all(db, limit=10)
    
    return templates.TemplateResponse(
        "send_plans.html",
        {
            "request": request,
            "user": current_user,
            "team_members": team_members,
            "recent_plans": recent_plans
        }
    )

@router.post("/plans")
async def create_plan(
    request: Request,
    team_member_id: int = Form(...),
    description: str = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Create new plan"""
    image_url = None
    if image and image.filename:
        image_url = await save_uploaded_file(image, "plans")
    
    plan_data = TeamMemberPlanCreate(
        team_member_id=team_member_id,
        description=description,
        image_url=image_url
    )
    
    db_plan = await team_member_plan.create(db, current_user["user_id"], plan_data)
    
    # Return HTML snippet for HTMX
    return HTMLResponse(f"""
    <div class="card mb-3" id="plan-{db_plan.id}">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h5 class="card-title">Plan #{db_plan.id}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">
                        To: {db_plan.team_member.name}
                    </h6>
                    <p class="card-text">{db_plan.description}</p>
                    {f'<img src="{db_plan.image_url}" class="img-fluid mt-2" style="max-height: 200px;">' if db_plan.image_url else ''}
                    <p class="card-text mt-2">
                        <small class="text-muted">
                            Sent by {db_plan.admin.name} at {db_plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}
                        </small>
                    </p>
                </div>
                <button class="btn btn-sm btn-danger"
                        hx-delete="/admin/plans/{db_plan.id}"
                        hx-confirm="Are you sure you want to delete this plan?"
                        hx-target="#plan-{db_plan.id}"
                        hx-swap="outerHTML">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    </div>
    """)

@router.delete("/plans/{plan_id}")
async def delete_plan(
    request: Request,
    plan_id: int,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Delete plan"""
    db_plan = await team_member_plan.get_by_id(db, plan_id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Delete image if exists
    if db_plan.image_url:
        await delete_file(db_plan.image_url)
    
    # Delete plan
    await team_member_plan.delete(db, plan_id)
    
    # Return empty response (card will be removed)
    return HTMLResponse("")

# Online Time Reports
@router.get("/online-time", response_class=HTMLResponse)
async def online_time_report(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Online time report"""
    # Get session statistics
    session_stats = await user_session.get_session_stats(db)
    
    # Get active sessions
    active_sessions = await user_session.get_active_sessions(db)
    
    # Get today's sessions
    today_sessions = await user_session.get_today_sessions(db)
    
    return templates.TemplateResponse(
        "online_time_report.html",
        {
            "request": request,
            "user": current_user,
            "session_stats": session_stats,
            "active_sessions": active_sessions,
            "today_sessions": today_sessions
        }
    )