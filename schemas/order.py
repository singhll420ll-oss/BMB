"""
Pydantic schemas for Order model
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models.order import OrderStatus

class OrderItemCreate(BaseModel):
    """Schema for creating an order item"""
    menu_item_id: int
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    """Schema for creating a new order"""
    service_id: int
    address: str = Field(..., min_length=5)
    notes: Optional[str] = None
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    """Schema for updating an order"""
    assigned_to: Optional[int] = None
    status: Optional[OrderStatus] = None
    otp: Optional[str] = None
    otp_expiry: Optional[datetime] = None
    delivery_confirmed_at: Optional[datetime] = None

class OrderItemResponse(BaseModel):
    """Schema for order item response"""
    id: int
    menu_item_id: int
    menu_item_name: str
    quantity: int
    price_at_time: float
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    """Schema for order response"""
    id: int
    customer_id: int
    customer_name: str
    service_id: int
    service_name: str
    total_amount: float
    address: str
    notes: Optional[str]
    status: str
    assigned_to: Optional[int]
    assigned_to_name: Optional[str]
    otp: Optional[str]
    otp_expiry: Optional[datetime]
    delivery_confirmed_at: Optional[datetime]
    created_at: datetime
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True
