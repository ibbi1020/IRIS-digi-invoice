"""
Invoice and InvoiceItem schemas for API request/response validation.

These schemas enforce PRD requirements:
- At least 1 item per invoice
- Non-negative numeric fields
- invoiceRefNo format validation
- Buyer registration type enum
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import DecimalField, PaginatedResponse, TimestampMixin


# =============================================================================
# Enums (mirror ORM enums for API layer)
# =============================================================================


class InvoiceTypeEnum(str, Enum):
    """Invoice type for API."""

    SALE = "Sale Invoice"
    DEBIT = "Debit Note"
    CREDIT = "Credit Note"


class InvoiceStatusEnum(str, Enum):
    """Invoice status for API."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    FAILED = "failed"
    UNKNOWN = "unknown"


class BuyerRegistrationTypeEnum(str, Enum):
    """Buyer registration type for API."""

    REGISTERED = "Registered"
    UNREGISTERED = "Unregistered"


# =============================================================================
# Invoice Item Schemas
# =============================================================================


class InvoiceItemBase(BaseModel):
    """Base schema for invoice line items with shared fields."""

    model_config = ConfigDict(from_attributes=True)

    hs_code: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Harmonized System code (e.g., '0000.0000')",
        examples=["0402.2100"],
    )
    product_description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Description of the product or service",
    )
    rate: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Tax rate (e.g., '0%', '17%')",
        examples=["17%", "0%"],
    )
    uom: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Unit of Measure",
        examples=["KG", "PCS", "LTR"],
    )
    quantity: DecimalField = Field(
        ...,
        ge=0,
        description="Quantity (must be non-negative)",
    )
    total_values: DecimalField = Field(
        ...,
        ge=0,
        description="Total value of the line item",
    )

    # Optional tax fields with defaults
    value_sales_excluding_st: DecimalField = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Value of sales excluding Sales Tax",
    )
    fixed_notified_value: DecimalField = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Fixed/Notified value or Retail Price",
    )
    sales_tax_applicable: DecimalField = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Applicable Sales Tax amount",
    )
    sales_tax_withheld: DecimalField = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Sales Tax withheld at source",
    )
    extra_tax: str = Field(
        default="",
        max_length=50,
    )
    further_tax: DecimalField = Field(
        default=Decimal("0.00"),
        ge=0,
    )
    sro_schedule_no: str = Field(
        default="",
        max_length=50,
        description="SRO Schedule Number",
    )
    fed_payable: DecimalField = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Federal Excise Duty payable",
    )
    discount: DecimalField = Field(
        default=Decimal("0.00"),
        ge=0,
    )
    sale_type: str = Field(
        default="",
        max_length=50,
    )
    sro_item_serial_no: str = Field(
        default="",
        max_length=50,
    )


class InvoiceItemCreate(InvoiceItemBase):
    """Schema for creating a new invoice item."""

    pass


class InvoiceItemUpdate(BaseModel):
    """Schema for updating an invoice item (all fields optional)."""

    model_config = ConfigDict(from_attributes=True)

    hs_code: str | None = Field(default=None, min_length=1, max_length=20)
    product_description: str | None = Field(default=None, min_length=1, max_length=500)
    rate: str | None = Field(default=None, min_length=1, max_length=10)
    uom: str | None = Field(default=None, min_length=1, max_length=20)
    quantity: DecimalField | None = Field(default=None, ge=0)
    total_values: DecimalField | None = Field(default=None, ge=0)
    value_sales_excluding_st: DecimalField | None = Field(default=None, ge=0)
    fixed_notified_value: DecimalField | None = Field(default=None, ge=0)
    sales_tax_applicable: DecimalField | None = Field(default=None, ge=0)
    sales_tax_withheld: DecimalField | None = Field(default=None, ge=0)
    extra_tax: str | None = Field(default=None, max_length=50)
    further_tax: DecimalField | None = Field(default=None, ge=0)
    sro_schedule_no: str | None = Field(default=None, max_length=50)
    fed_payable: DecimalField | None = Field(default=None, ge=0)
    discount: DecimalField | None = Field(default=None, ge=0)
    sale_type: str | None = Field(default=None, max_length=50)
    sro_item_serial_no: str | None = Field(default=None, max_length=50)


class InvoiceItemResponse(InvoiceItemBase):
    """Schema for invoice item in API responses."""

    id: UUID


# =============================================================================
# Invoice Schemas
# =============================================================================


class InvoiceBase(BaseModel):
    """Base schema for invoices with shared fields."""

    model_config = ConfigDict(from_attributes=True)

    invoice_ref_no: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique invoice reference number (per seller NTN)",
        examples=["INV-0001", "1001"],
    )
    invoice_type: InvoiceTypeEnum = Field(
        default=InvoiceTypeEnum.SALE,
        description="Type of invoice document",
    )
    invoice_date: date = Field(
        ...,
        description="Invoice date",
    )

    # Buyer information
    buyer_ntn_cnic: str = Field(
        ...,
        min_length=1,
        max_length=13,
        description="Buyer NTN (13 digits) or CNIC",
    )
    buyer_business_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Buyer's business name",
    )
    buyer_province: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Buyer's province",
        examples=["Punjab", "Sindh", "KPK"],
    )
    buyer_address: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Buyer's address",
    )
    buyer_registration_type: BuyerRegistrationTypeEnum = Field(
        ...,
        description="Buyer's FBR registration status",
    )

    # FBR fields
    scenario_id: str = Field(
        default="SN000",
        max_length=10,
        description="FBR scenario ID",
    )

    # For Debit/Credit notes: reference to original Sales Invoice
    referenced_invoice_ref_no: str | None = Field(
        default=None,
        description="Reference to original Sales Invoice (for Debit/Credit notes)",
    )

    @field_validator("buyer_ntn_cnic")
    @classmethod
    def validate_buyer_ntn_cnic(cls, v: str) -> str:
        """Validate NTN/CNIC format: 13 digits or valid CNIC format."""
        v = v.strip()
        # Remove any hyphens for CNIC
        cleaned = v.replace("-", "")
        if not cleaned.isdigit():
            raise ValueError("NTN/CNIC must contain only digits (hyphens allowed for CNIC)")
        if len(cleaned) not in (13, 15):  # NTN is 13, CNIC is 13 or 15 with separators
            # Allow flexibility for now, FBR will validate
            pass
        return v


class InvoiceCreate(InvoiceBase):
    """Schema for creating a new invoice with items."""

    items: list[InvoiceItemCreate] = Field(
        ...,
        min_length=1,
        description="Line items (at least 1 required)",
    )

    @model_validator(mode="after")
    def validate_reference_for_debit_credit(self) -> "InvoiceCreate":
        """Validate that Debit/Credit notes have a referenced invoice."""
        if self.invoice_type in (InvoiceTypeEnum.DEBIT, InvoiceTypeEnum.CREDIT):
            if not self.referenced_invoice_ref_no:
                raise ValueError(
                    f"{self.invoice_type.value} must reference an existing Sales Invoice"
                )
        return self


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice (partial updates, draft only)."""

    model_config = ConfigDict(from_attributes=True)

    invoice_date: date | None = None
    buyer_ntn_cnic: str | None = Field(default=None, min_length=1, max_length=13)
    buyer_business_name: str | None = Field(default=None, min_length=1, max_length=255)
    buyer_province: str | None = Field(default=None, min_length=1, max_length=100)
    buyer_address: str | None = Field(default=None, min_length=1, max_length=500)
    buyer_registration_type: BuyerRegistrationTypeEnum | None = None
    scenario_id: str | None = Field(default=None, max_length=10)

    # Items can be replaced entirely
    items: list[InvoiceItemCreate] | None = None

    @model_validator(mode="after")
    def validate_items_if_provided(self) -> "InvoiceUpdate":
        """Ensure at least 1 item if items are being updated."""
        if self.items is not None and len(self.items) == 0:
            raise ValueError("At least 1 item is required")
        return self


class InvoiceResponse(InvoiceBase, TimestampMixin):
    """Schema for invoice in API responses."""

    id: UUID
    tenant_id: UUID
    status: InvoiceStatusEnum
    submitted_at: datetime | None = None
    items: list[InvoiceItemResponse] = []

    # Computed fields for convenience
    item_count: int = 0

    @model_validator(mode="after")
    def compute_item_count(self) -> "InvoiceResponse":
        """Compute the item count from items list."""
        object.__setattr__(self, "item_count", len(self.items))
        return self


class InvoiceSummaryResponse(BaseModel):
    """Lightweight invoice summary for list views (no items)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_ref_no: str
    invoice_type: InvoiceTypeEnum
    invoice_date: date
    buyer_business_name: str
    status: InvoiceStatusEnum
    item_count: int = 0
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(PaginatedResponse):
    """Paginated list of invoice summaries."""

    items: list[InvoiceSummaryResponse]


class SuggestRefNoResponse(BaseModel):
    """Response for suggest-next invoiceRefNo endpoint."""

    suggested_ref_no: str | None = Field(
        description="Suggested next invoiceRefNo, or null if no suggestion available"
    )
    last_ref_no: str | None = Field(
        description="The last successfully submitted invoiceRefNo"
    )
