"""
CRUD operations for Service model
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List

from models.service import Service
from schemas.service import ServiceCreate, ServiceUpdate

class ServiceCRUD:
    """CRUD operations for Service model"""
    
    @staticmethod
    async def create(db: AsyncSession, service_data: ServiceCreate) -> Service:
        """Create a new service"""
        db_service = Service(
            name=service_data.name,
            description=service_data.description,
            image_url=service_data.image_url
        )
        db.add(db_service)
        await db.commit()
        await db.refresh(db_service)
        return db_service
    
    @staticmethod
    async def get_by_id(db: AsyncSession, service_id: int) -> Optional[Service]:
        """Get service by ID with menu items"""
        result = await db.execute(
            select(Service)
            .where(Service.id == service_id)
            .options(selectinload(Service.menu_items))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get all services"""
        result = await db.execute(
            select(Service)
            .order_by(Service.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update(db: AsyncSession, service_id: int, service_data: ServiceUpdate) -> Optional[Service]:
        """Update service information"""
        update_data = service_data.dict(exclude_unset=True)
        
        if update_data:
            await db.execute(
                update(Service)
                .where(Service.id == service_id)
                .values(**update_data)
            )
            await db.commit()
        
        return await ServiceCRUD.get_by_id(db, service_id)
    
    @staticmethod
    async def delete(db: AsyncSession, service_id: int) -> bool:
        """Delete a service"""
        result = await db.execute(
            delete(Service).where(Service.id == service_id)
        )
        await db.commit()
        return result.rowcount > 0

# Create instance
service = ServiceCRUD()
