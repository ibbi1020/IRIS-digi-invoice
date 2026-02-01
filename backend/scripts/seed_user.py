"""
Script to seed initial test data for development.

Usage:
    python -m scripts.seed_user
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models import Tenant, User
from app.utils.security import hash_password


async def seed_test_user() -> None:
    """Create a test tenant and user for development."""
    async with async_session_maker() as db:
        # Check if test tenant already exists
        result = await db.execute(
            select(Tenant).where(Tenant.seller_ntn == "1234567890123")
        )
        existing_tenant = result.scalar_one_or_none()

        if existing_tenant:
            print("Test tenant already exists, skipping seed...")
            return

        # Create test tenant
        tenant = Tenant(
            seller_ntn="1234567890123",
            business_name="Test Company Ltd",
            province="Punjab",
            address="123 Test Street, Lahore",
            fbr_token="0a1ad30e-3ef3-318c-ac42-153513973521",  # Sandbox token
        )
        db.add(tenant)
        await db.flush()

        # Create test user
        user = User(
            tenant_id=tenant.id,
            email="test@example.com",
            password_hash=hash_password("password123"),
            full_name="Test User",
        )
        db.add(user)
        await db.commit()

        print("✅ Seed data created successfully!")
        print(f"   Tenant NTN: {tenant.seller_ntn}")
        print(f"   User Email: {user.email}")
        print(f"   Password: password123")


if __name__ == "__main__":
    asyncio.run(seed_test_user())
