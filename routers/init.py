"""
Routers package initialization
"""

from routers.auth import router as auth_router
from routers.customer import router as customer_router
from routers.team_member import router as team_member_router
from routers.admin import router as admin_router
from routers.public import router as public_router

__all__ = [
    "auth_router",
    "customer_router",
    "team_member_router",
    "admin_router",
    "public_router"
]
