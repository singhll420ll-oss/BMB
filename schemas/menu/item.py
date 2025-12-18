"""
Pydantic schemas for MenuItem model
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MenuItemCreate(BaseModel):
    """Schema for creating a new menu item"""
    service_id: int
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    image_url: Optional[str] = None

class MenuItemUpdate(BaseModel):
    """Schema for updating a menu item"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = None

class MenuItemResponse(BaseModel):
    """Schema for menu item response"""
    id: int
    service_id: int
    name: str
    description: Optional[str]
    price: float
    image_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
