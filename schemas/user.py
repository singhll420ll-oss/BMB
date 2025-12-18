"""
Pydantic schemas for User model
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re

from models.user import UserRole

class UserCreate(BaseModel):
    """Schema for creating a new user"""
    name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6)
    address: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if not re.match(r'^\+?[0-9\s\-\(\)]{10,20}$', v):
            raise ValueError('Invalid phone number format')
        return v

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    address: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)

class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str
    role: UserRole

class UserResponse(BaseModel):
    """Schema for user response (without password)"""
    id: int
    name: str
    username: str
    email: str
    phone: str
    address: Optional[str]
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True
