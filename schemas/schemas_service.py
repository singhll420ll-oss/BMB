"""
Pydantic schemas for Service model
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ServiceCreate(BaseModel):
    """Schema for creating a new service"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = None

class ServiceUpdate(BaseModel):
    """Schema for updating a service"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = None

class ServiceResponse(BaseModel):
    """Schema for service response"""
    id: int
    name: str
    description: Optional[str]
    image_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True