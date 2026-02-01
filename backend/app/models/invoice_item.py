"""
InvoiceItem model - line items for an invoice.
"""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.invoice import Invoice


class InvoiceItem(Base):
    """
    Line item for an invoice.
    
    Each invoice must have at least one item as per FBR requirements.
    """

    __tablename__ = "invoice_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Invoice relationship
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Item identification
    hs_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Harmonized System code (e.g., 0000.0000)",
    )
    product_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    # Pricing and quantity
    rate: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Tax rate (e.g., '0%', '17%')",
    )
    uom: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Unit of Measure",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4),
        nullable=False,
    )
    total_values: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )
    
    # Tax fields
    value_sales_excluding_st: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Value of sales excluding Sales Tax",
    )
    fixed_notified_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Fixed/Notified value or Retail Price",
    )
    sales_tax_applicable: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )
    sales_tax_withheld: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Sales Tax withheld at source",
    )
    extra_tax: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
    )
    further_tax: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )
    
    # Additional fields
    sro_schedule_no: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
        comment="SRO Schedule Number",
    )
    fed_payable: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Federal Excise Duty payable",
    )
    discount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )
    sale_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
    )
    sro_item_serial_no: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"<InvoiceItem(hs_code={self.hs_code}, qty={self.quantity})>"
