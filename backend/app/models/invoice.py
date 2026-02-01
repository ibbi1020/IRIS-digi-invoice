"""
Invoice model - represents Sales Invoices, Debit Notes, and Credit Notes.
"""

import enum
import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.invoice_item import InvoiceItem
    from app.models.submission_attempt import SubmissionAttempt
    from app.models.tenant import Tenant


class InvoiceType(str, enum.Enum):
    """Type of invoice document."""

    SALE = "Sale Invoice"
    DEBIT = "Debit Note"
    CREDIT = "Credit Note"


class InvoiceStatus(str, enum.Enum):
    """Status of the invoice submission."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    FAILED = "failed"
    UNKNOWN = "unknown"


class BuyerRegistrationType(str, enum.Enum):
    """Buyer's registration status with FBR."""

    REGISTERED = "Registered"
    UNREGISTERED = "Unregistered"


class Invoice(Base):
    """
    Invoice model for Sales Invoices, Debit Notes, and Credit Notes.
    
    The invoiceRefNo is unique per tenant (seller NTN) and is the key
    identifier for FBR submissions.
    """

    __tablename__ = "invoices"
    
    # Unique constraint: invoiceRefNo must be unique per tenant
    __table_args__ = (
        UniqueConstraint("tenant_id", "invoice_ref_no", name="uq_tenant_invoice_ref"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Tenant relationship
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Invoice identification
    invoice_ref_no: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Unique invoice reference number per tenant",
    )
    invoice_type: Mapped[InvoiceType] = mapped_column(
        Enum(InvoiceType),
        nullable=False,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    
    # For Debit/Credit notes: reference to original Sales Invoice
    referenced_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to original Sales Invoice (for debit/credit notes)",
    )
    
    # Buyer information
    buyer_ntn_cnic: Mapped[str] = mapped_column(
        String(13),
        nullable=False,
        comment="Buyer NTN or CNIC",
    )
    buyer_business_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    buyer_province: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    buyer_address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    buyer_registration_type: Mapped[BuyerRegistrationType] = mapped_column(
        Enum(BuyerRegistrationType),
        nullable=False,
    )
    
    # FBR scenario
    scenario_id: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="SN000",
        comment="FBR scenario ID",
    )
    
    # Submission status
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus),
        nullable=False,
        default=InvoiceStatus.DRAFT,
    )
    
    # Metadata
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
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="invoices")
    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    attempts: Mapped[list["SubmissionAttempt"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="SubmissionAttempt.attempt_number",
    )
    referenced_invoice: Mapped["Invoice | None"] = relationship(
        remote_side=[id],
        foreign_keys=[referenced_invoice_id],
    )

    def __repr__(self) -> str:
        return f"<Invoice(ref={self.invoice_ref_no}, type={self.invoice_type.value}, status={self.status.value})>"
