"""
CRUD operations for MenuItem model
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Optional, List

from models.menu_item import MenuItem
from schemas.menu_item import MenuItemCreate, MenuItemUpdate

class MenuItemCRUD:
    """CRUD operations for MenuItem model"""
    
    @staticmethod
    async def create(db: AsyncSession, menu_item_data: MenuItemCreate) -> MenuItem:
        """Create a new menu item"""
        db_menu_item = MenuItem(
            service_id=menu_item_data.service_id,
            name=menu_item_data.name,
            description=menu_item_data.description,
            price=menu_item_data.price,
            image_url=menu_item_data.image_url
        )
        db.add(db_menu_item)
        await db.commit()
        await db.refresh(db_menu_item)
        return db_menu_item
    
    @staticmethod
    async def get_by_id(db: AsyncSession, menu_item_id: int) -> Optional[MenuItem]:
        """Get menu item by ID"""
        result = await db.execute(
            select(MenuItem).where(MenuItem.id == menu_item_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_service(db: AsyncSession, service_id: int) -> List[MenuItem]:
        """Get all menu items for a service"""
        result = await db.execute(
            select(MenuItem)
            .where(MenuItem.service_id == service_id)
            .order_by(MenuItem.name)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update(db: AsyncSession, menu_item_id: int, menu_item_data: MenuItemUpdate) -> Optional[MenuItem]:
        """Update menu item information"""
        update_data = menu_item_data.dict(exclude_unset=True)
        
        if update_data:
            await db.execute(
                update(MenuItem)
                .where(MenuItem.id == menu_item_id)
                .values(**update_data)
            )
            await db.commit()
        
        return await MenuItemCRUD.get_by_id(db, menu_item_id)
    
    @staticmethod
    async def delete(db: AsyncSession, menu_item_id: int) -> bool:
        """Delete a menu item"""
        result = await db.execute(
            delete(MenuItem).where(MenuItem.id == menu_item_id)
        )
        await db.commit()
        return result.rowcount > 0

# Create instance
menu_item = MenuItemCRUD()