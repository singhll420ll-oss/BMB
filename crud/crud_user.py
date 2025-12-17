"""
CRUD operations for User model
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List

from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash, verify_password

class UserCRUD:
    """CRUD operations for User model"""
    
    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            name=user_data.name,
            username=user_data.username,
            email=user_data.email,
            phone=user_data.phone,
            hashed_password=hashed_password,
            address=user_data.address,
            role=user_data.role
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
        """Get user by phone"""
        result = await db.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        result = await db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_by_role(db: AsyncSession, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role"""
        result = await db.execute(
            select(User)
            .where(User.role == role)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update(db: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        update_data = user_data.dict(exclude_unset=True)
        
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        if update_data:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
            )
            await db.commit()
        
        return await UserCRUD.get_by_id(db, user_id)
    
    @staticmethod
    async def delete(db: AsyncSession, user_id: int) -> bool:
        """Delete a user"""
        result = await db.execute(
            delete(User).where(User.id == user_id)
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def authenticate(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate user"""
        user = await UserCRUD.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

# Create instance
user = UserCRUD()