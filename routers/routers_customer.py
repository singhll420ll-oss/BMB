"""
Customer routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

from database import get_db
from core.security import get_current_user
from crud import service, menu_item, order, user_session
from schemas.order import OrderCreate, OrderItemCreate
from models.user import UserRole

router = APIRouter(prefix="/customer", tags=["customer"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def customer_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.CUSTOMER])),
    db: AsyncSession = Depends(get_db)
):
    """Customer dashboard"""
    # Get user's recent orders
    recent_orders = await order.get_by_customer(db, current_user["user_id"], limit=5)
    
    # Get all services
    services = await service.get_all(db)
    
    return templates.TemplateResponse(
        "customer_dashboard.html",
        {
            "request": request,
            "user": current_user,
            "recent_orders": recent_orders,
            "services": services
        }
    )

@router.get("/services", response_class=HTMLResponse)
async def customer_services(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.CUSTOMER])),
    db: AsyncSession = Depends(get_db)
):
    """Services list page"""
    services = await service.get_all(db)
    return templates.TemplateResponse(
        "services.html",
        {
            "request": request,
            "user": current_user,
            "services": services
        }
    )

@router.get("/service/{service_id}/menu", response_class=HTMLResponse)
async def service_menu(
    request: Request,
    service_id: int,
    current_user: dict = Depends(get_current_user([UserRole.CUSTOMER])),
    db: AsyncSession = Depends(get_db)
):
    """Service menu page"""
    # Get service with menu items
    db_service = await service.get_by_id(db, service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return templates.TemplateResponse(
        "service_menu.html",
        {
            "request": request,
            "user": current_user,
            "service": db_service,
            "menu_items": db_service.menu_items
        }
    )

@router.get("/cart", response_class=HTMLResponse)
async def cart_page(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.CUSTOMER])),
    db: AsyncSession = Depends(get_db)
):
    """Cart page"""
    # Get cart from session or query string
    cart_data = request.session.get("cart", {})
    service_id = cart_data.get("service_id")
    
    if not service_id:
        # Try to get from query string
        service_id = request.query_params.get("service_id")
        if service_id:
            cart_data["service_id"] = int(service_id)
    
    service_info = None
    menu_items_info = []
    total_amount = 0
    
    if service_id:
        # Get service info
        db_service = await service.get_by_id(db, int(service_id))
        if db_service:
            service_info = {
                "id": db_service.id,
                "name": db_service.name,
                "image_url": db_service.image_url
            }
            
            # Get menu items info
            items = cart_data.get("items", {})
            for menu_item_id, quantity in items.items():
                menu_item_info = await menu_item.get_by_id(db, int(menu_item_id))
                if menu_item_info:
                    item_total = menu_item_info.price * quantity
                    total_amount += item_total
                    
                    menu_items_info.append({
                        "id": menu_item_info.id,
                        "name": menu_item_info.name,
                        "price": menu_item_info.price,
                        "quantity": quantity,
                        "total": item_total,
                        "image_url": menu_item_info.image_url
                    })
    
    return templates.TemplateResponse(
        "cart.html",
        {
            "request": request,
            "user": current_user,
            "service": service_info,
            "cart_items": menu_items_info,
            "total_amount": total_amount,
            "cart_data": json.dumps(cart_data)
        }
    )

@router.post("/add-to-cart")
async def add_to_cart(
    request: Request,
    service_id: int = Form(...),
    menu_item_id: int = Form(...),
    quantity: int = Form(1),
    current_user: dict = Depends(get_current_user([UserRole.CUSTOMER]))
):
    """Add item to cart"""
    # Initialize cart in session if not exists
    if "cart" not in request.session:
        request.session["cart"] = {}
    
    cart = request.session["cart"]
    
    # Set service ID
    cart["service_id"] = service_id
    
    # Initialize items dict if not exists
    if "items" not in cart:
        cart["items"] = {}
    
    # Add item
    items = cart["items"]
    item_key = str(menu_item_id)
    items[item_key] = items.get(item_key, 0) + quantity
    
    # Update session
    request.session["cart"] = cart
    
    # Redirect to cart page
    return RedirectResponse(
        url=f"/customer/cart?service_id={service_id}",
        status_code=303
    )

@router.post("/update-cart")
async def update_cart(
    request: Request,
    menu_item_id: int = Form(...),
    quantity: int = Form(...),
    current_user: dict = Depends(get_current_user([UserRole.CUSTOMER]))
):
    """Update cart item quantity"""
    cart = request.session.get("cart", {})
    items = cart.get("items", {})
    
    item_key = str(menu_item_id)
    
    if quantity <= 0:
        # Remove item
        if item_key in items:
            del items[item_key]
    else:
        # Update quantity
        items[item_key] = quantity
    
    # Update session
    cart["items"] = items
    request.session["cart"] = cart
    
    # Redirect back to cart
    return RedirectResponse(url="/customer/cart", status_code=303)

@router.post("/place-order")
async def place_order(
    request: Request,
    address: str = Form(...),
    notes: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user([UserRole.CUSTOMER])),
    db: AsyncSession = Depends(get_db)
):
    """Place order from cart"""
    cart = request.session.get("cart", {})
    
    if not cart or "service_id" not in cart or "items" not in cart:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Prepare order items
    order_items = []
    for menu_item_id, quantity in cart["items"].items():
        order_items.append(OrderItemCreate(
            menu_item_id=int(menu_item_id),
            quantity=quantity
        ))
    
    # Create order
    order_data = OrderCreate(
        service_id=cart["service_id"],
        address=address,
        notes=notes,
        items=order_items
    )
    
    # Save order
    db_order = await order.create(db, current_user["user_id"], order_data)
    
    # Clear cart
    request.session.pop("cart", None)
    
    # Redirect to orders page
    return RedirectResponse(url="/customer/my-orders", status_code=303)

@router.get("/my-orders", response_class=HTMLResponse)
async def my_orders(
    request: Request,
    current_user: dict = Depends(get_current_user([UserRole.CUSTOMER])),
    db: AsyncSession = Depends(get_db)
):
    """Customer's order history"""
    orders = await order.get_by_customer(db, current_user["user_id"])
    return templates.TemplateResponse(
        "my_orders.html",
        {
            "request": request,
            "user": current_user,
            "orders": orders
        }
    )

@router.get("/order/{order_id}", response_class=HTMLResponse)
async def order_details(
    request: Request,
    order_id: int,
    current_user: dict = Depends(get_current_user([UserRole.CUSTOMER])),
    db: AsyncSession = Depends(get_db)
):
    """Order details page"""
    db_order = await order.get_by_id(db, order_id)
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order belongs to current user
    if db_order.customer_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return templates.TemplateResponse(
        "order_details.html",
        {
            "request": request,
            "user": current_user,
            "order": db_order
        }
    )