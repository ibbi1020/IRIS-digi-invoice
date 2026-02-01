"""
Tenant model - represents a seller/company registered on the platform.

Each tenant has their own NTN and FBR credentials.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.user import User


class Tenant(Base):
    """
    Tenant model representing a seller/company.
    
    Each tenant is identified by their seller NTN and can have
    multiple users and invoices.
    """

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Seller identification (from FBR)
    seller_ntn: Mapped[str] = mapped_column(
        String(13),
        unique=True,
        index=True,
        nullable=False,
        comment="Seller National Tax Number (13 digits)",
    )
    business_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    province: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    # FBR integration credentials (encrypted in production)
    fbr_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="FBR Bearer token (user-provided for MVP)",
    )
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Tenant(ntn={self.seller_ntn}, name={self.business_name})>"
