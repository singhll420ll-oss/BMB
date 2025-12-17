"""
CRUD operations for Order model
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import random

from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.menu_item import MenuItem
from models.user import User
from schemas.order import OrderCreate, OrderUpdate

class OrderCRUD:
    """CRUD operations for Order model"""
    
    @staticmethod
    async def create(db: AsyncSession, customer_id: int, order_data: OrderCreate) -> Order:
        """Create a new order with items"""
        # Calculate total amount
        total_amount = 0
        menu_item_ids = [item.menu_item_id for item in order_data.items]
        
        # Get menu items prices
        result = await db.execute(
            select(MenuItem.id, MenuItem.price)
            .where(MenuItem.id.in_(menu_item_ids))
        )
        menu_items = {row.id: row.price for row in result}
        
        # Calculate total and prepare order items
        order_items = []
        for item in order_data.items:
            price = menu_items.get(item.menu_item_id)
            if price:
                total_amount += price * item.quantity
                order_items.append(OrderItem(
                    menu_item_id=item.menu_item_id,
                    quantity=item.quantity,
                    price_at_time=price
                ))
        
        # Create order
        db_order = Order(
            customer_id=customer_id,
            service_id=order_data.service_id,
            total_amount=total_amount,
            address=order_data.address,
            notes=order_data.notes,
            status=OrderStatus.PENDING.value
        )
        
        db.add(db_order)
        await db.flush()  # Get order ID
        
        # Add order items
        for order_item in order_items:
            order_item.order_id = db_order.id
            db.add(order_item)
        
        await db.commit()
        await db.refresh(db_order)
        return db_order
    
    @staticmethod
    async def get_by_id(db: AsyncSession, order_id: int) -> Optional[Order]:
        """Get order by ID with all relationships"""
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.customer),
                selectinload(Order.service),
                selectinload(Order.team_member),
                selectinload(Order.order_items).selectinload(OrderItem.menu_item)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_customer(db: AsyncSession, customer_id: int, skip: int = 0, limit: int = 50) -> List[Order]:
        """Get all orders for a customer"""
        result = await db.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(selectinload(Order.service))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_by_team_member(db: AsyncSession, team_member_id: int, skip: int = 0, limit: int = 50) -> List[Order]:
        """Get orders assigned to a team member"""
        result = await db.execute(
            select(Order)
            .where(Order.assigned_to == team_member_id)
            .options(
                selectinload(Order.customer),
                selectinload(Order.service)
            )
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_pending_orders(db: AsyncSession, skip: int = 0, limit: int = 50) -> List[Order]:
        """Get all pending orders"""
        result = await db.execute(
            select(Order)
            .where(Order.status == OrderStatus.PENDING.value)
            .options(
                selectinload(Order.customer),
                selectinload(Order.service)
            )
            .order_by(Order.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get all orders"""
        result = await db.execute(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.service)
            )
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update(db: AsyncSession, order_id: int, order_data: OrderUpdate) -> Optional[Order]:
        """Update order information"""
        update_data = order_data.dict(exclude_unset=True)
        
        if update_data:
            await db.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(**update_data)
            )
            await db.commit()
        
        return await OrderCRUD.get_by_id(db, order_id)
    
    @staticmethod
    async def delete(db: AsyncSession, order_id: int) -> bool:
        """Delete an order"""
        result = await db.execute(
            delete(Order).where(Order.id == order_id)
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def generate_otp(db: AsyncSession, order_id: int) -> Tuple[str, datetime]:
        """Generate OTP for order delivery"""
        otp = str(random.randint(1000, 9999))
        otp_expiry = datetime.utcnow() + timedelta(minutes=5)
        
        await db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(otp=otp, otp_expiry=otp_expiry)
        )
        await db.commit()
        
        return otp, otp_expiry
    
    @staticmethod
    async def verify_otp(db: AsyncSession, order_id: int, otp: str) -> bool:
        """Verify OTP for order delivery"""
        result = await db.execute(
            select(Order.otp, Order.otp_expiry)
            .where(Order.id == order_id)
        )
        order_data = result.first()
        
        if not order_data:
            return False
        
        stored_otp, otp_expiry = order_data
        
        if not stored_otp or not otp_expiry:
            return False
        
        if datetime.utcnow() > otp_expiry:
            return False
        
        return stored_otp == otp
    
    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        """Get order statistics"""
        # Total orders
        result = await db.execute(select(func.count(Order.id)))
        total_orders = result.scalar()
        
        # Today's orders
        result = await db.execute(
            select(func.count(Order.id))
            .where(func.date(Order.created_at) == func.current_date())
        )
        today_orders = result.scalar()
        
        # Pending orders
        result = await db.execute(
            select(func.count(Order.id))
            .where(Order.status == OrderStatus.PENDING.value)
        )
        pending_orders = result.scalar()
        
        # Revenue
        result = await db.execute(select(func.sum(Order.total_amount)))
        total_revenue = result.scalar() or 0
        
        # Today's revenue
        result = await db.execute(
            select(func.sum(Order.total_amount))
            .where(func.date(Order.created_at) == func.current_date())
        )
        today_revenue = result.scalar() or 0
        
        return {
            "total_orders": total_orders,
            "today_orders": today_orders,
            "pending_orders": pending_orders,
            "total_revenue": total_revenue,
            "today_revenue": today_revenue
        }

# Create instance
order = OrderCRUD()