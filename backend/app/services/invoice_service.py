"""
Invoice service - business logic for invoice operations.

Implements PRD requirements:
- invoiceRefNo uniqueness per tenant
- Blocking for submitted/unknown status
- Debit/Credit reference validation
- Suggest-next algorithm
"""

from datetime import date
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import InvoiceItem, Tenant
from app.models.invoice import Invoice, InvoiceStatus, InvoiceType
from app.schemas.common import PaginationParams
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate, InvoiceUpdate
from app.services.fbr_service import FBRService
from app.utils.invoice_ref import (
    suggest_next_ref_no,
    validate_ref_no_format,
)


# =============================================================================
# Exceptions
# =============================================================================


class InvoiceNotFoundError(Exception):
    """Raised when invoice is not found."""

    def __init__(self, invoice_id: UUID):
        self.invoice_id = invoice_id
        super().__init__(f"Invoice not found: {invoice_id}")


class InvoiceRefNoExistsError(Exception):
    """Raised when invoiceRefNo already exists for tenant."""

    def __init__(self, ref_no: str, status: InvoiceStatus | None = None):
        self.ref_no = ref_no
        self.status = status
        message = f"Invoice reference '{ref_no}' already exists"
        if status:
            message += f" with status '{status.value}'"
        super().__init__(message)


class InvoiceRefNoBlockedError(Exception):
    """Raised when invoiceRefNo is blocked due to submitted/unknown status."""

    def __init__(self, ref_no: str, status: InvoiceStatus):
        self.ref_no = ref_no
        self.status = status
        super().__init__(
            f"Invoice reference '{ref_no}' is blocked (status: {status.value}). "
            "Cannot reuse a reference that has been submitted or has unknown outcome."
        )


class InvoiceNotDraftError(Exception):
    """Raised when trying to modify a non-draft invoice."""

    def __init__(self, invoice_id: UUID, status: InvoiceStatus):
        self.invoice_id = invoice_id
        self.status = status
        super().__init__(
            f"Invoice {invoice_id} cannot be modified (status: {status.value}). "
            "Only draft invoices can be updated or deleted."
        )


class ReferencedInvoiceNotFoundError(Exception):
    """Raised when referenced Sales Invoice for Debit/Credit note is not found."""

    def __init__(self, ref_no: str):
        self.ref_no = ref_no
        super().__init__(
            f"Referenced Sales Invoice '{ref_no}' not found or not in submitted status"
        )


# =============================================================================
# Query Functions
# =============================================================================


async def get_invoice_by_id(
    db: AsyncSession,
    tenant_id: UUID,
    invoice_id: UUID,
    *,
    with_items: bool = True,
) -> Invoice | None:
    """
    Get invoice by ID, scoped to tenant.

    Args:
        db: Database session
        tenant_id: Tenant UUID for isolation
        invoice_id: Invoice UUID
        with_items: Whether to eagerly load items

    Returns:
        Invoice or None if not found
    """
    query = select(Invoice).where(
        and_(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
    )

    if with_items:
        query = query.options(selectinload(Invoice.items))

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_invoice_by_ref_no(
    db: AsyncSession,
    tenant_id: UUID,
    ref_no: str,
) -> Invoice | None:
    """
    Get invoice by reference number, scoped to tenant.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        ref_no: Invoice reference number

    Returns:
        Invoice or None if not found
    """
    result = await db.execute(
        select(Invoice).where(
            and_(Invoice.invoice_ref_no == ref_no, Invoice.tenant_id == tenant_id)
        )
    )
    return result.scalar_one_or_none()


async def list_invoices(
    db: AsyncSession,
    tenant_id: UUID,
    pagination: PaginationParams,
    *,
    status_filter: InvoiceStatus | None = None,
    type_filter: InvoiceType | None = None,
) -> tuple[list[Invoice], int]:
    """
    List invoices for a tenant with pagination and optional filters.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        pagination: Pagination parameters
        status_filter: Optional status filter
        type_filter: Optional type filter

    Returns:
        Tuple of (invoices list, total count)
    """
    # Base query
    base_query = select(Invoice).where(Invoice.tenant_id == tenant_id)

    # Apply filters
    if status_filter:
        base_query = base_query.where(Invoice.status == status_filter)
    if type_filter:
        base_query = base_query.where(Invoice.invoice_type == type_filter)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = (
        base_query.options(selectinload(Invoice.items))
        .order_by(Invoice.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    result = await db.execute(query)
    invoices = list(result.scalars().all())

    return invoices, total


# =============================================================================
# Validation Functions
# =============================================================================


async def check_ref_no_availability(
    db: AsyncSession,
    tenant_id: UUID,
    ref_no: str,
    *,
    exclude_invoice_id: UUID | None = None,
) -> None:
    """
    Check if invoiceRefNo is available for use.

    PRD rules:
    - Warn + block if already used successfully
    - Block if outcome is unknown (conservative)

    Args:
        db: Database session
        tenant_id: Tenant UUID
        ref_no: Invoice reference number to check
        exclude_invoice_id: Exclude this invoice from check (for updates)

    Raises:
        InvoiceRefNoExistsError: If ref exists with DRAFT status
        InvoiceRefNoBlockedError: If ref exists with SUBMITTED/UNKNOWN status
    """
    query = select(Invoice).where(
        and_(Invoice.invoice_ref_no == ref_no, Invoice.tenant_id == tenant_id)
    )

    if exclude_invoice_id:
        query = query.where(Invoice.id != exclude_invoice_id)

    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        if existing.status in (InvoiceStatus.SUBMITTED, InvoiceStatus.UNKNOWN):
            raise InvoiceRefNoBlockedError(ref_no, existing.status)
        elif existing.status == InvoiceStatus.FAILED:
            # Failed can be retried, but we need a new invoice
            raise InvoiceRefNoExistsError(ref_no, existing.status)
        else:
            # Draft exists
            raise InvoiceRefNoExistsError(ref_no, existing.status)


async def validate_referenced_invoice(
    db: AsyncSession,
    tenant_id: UUID,
    ref_no: str,
) -> Invoice:
    """
    Validate that a referenced Sales Invoice exists and is submitted.

    PRD rule: Debit/Credit notes must reference an existing Sales Invoice
    that is in "Recorded/Submitted Success" state.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        ref_no: Reference number of the Sales Invoice

    Returns:
        The referenced Invoice

    Raises:
        ReferencedInvoiceNotFoundError: If not found or not submitted
    """
    result = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.invoice_ref_no == ref_no,
                Invoice.tenant_id == tenant_id,
                Invoice.invoice_type == InvoiceType.SALE,
                Invoice.status == InvoiceStatus.SUBMITTED,
            )
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise ReferencedInvoiceNotFoundError(ref_no)

    return invoice


# =============================================================================
# CRUD Functions
# =============================================================================


async def create_invoice(
    db: AsyncSession,
    tenant: Tenant,
    data: InvoiceCreate,
) -> Invoice:
    """
    Create a new draft invoice with items.

    Args:
        db: Database session
        tenant: Tenant object
        data: Invoice creation data

    Returns:
        Created Invoice

    Raises:
        InvoiceRefNoExistsError: If ref already exists
        InvoiceRefNoBlockedError: If ref is blocked
        ReferencedInvoiceNotFoundError: If Debit/Credit reference is invalid
    """
    # Check ref availability
    await check_ref_no_availability(db, tenant.id, data.invoice_ref_no)

    # For Debit/Credit notes, validate the reference
    referenced_invoice_id = None
    if data.invoice_type.value in (InvoiceType.DEBIT.value, InvoiceType.CREDIT.value):
        if data.referenced_invoice_ref_no:
            referenced = await validate_referenced_invoice(
                db, tenant.id, data.referenced_invoice_ref_no
            )
            referenced_invoice_id = referenced.id

    # Create invoice
    invoice = Invoice(
        tenant_id=tenant.id,
        invoice_ref_no=data.invoice_ref_no,
        invoice_type=InvoiceType(data.invoice_type.value),
        invoice_date=data.invoice_date,
        buyer_ntn_cnic=data.buyer_ntn_cnic,
        buyer_business_name=data.buyer_business_name,
        buyer_province=data.buyer_province,
        buyer_address=data.buyer_address,
        buyer_registration_type=data.buyer_registration_type.value,
        scenario_id=data.scenario_id,
        referenced_invoice_id=referenced_invoice_id,
        status=InvoiceStatus.DRAFT,
    )
    db.add(invoice)
    await db.flush()

    # Create items
    for item_data in data.items:
        item = _create_invoice_item(invoice.id, item_data)
        db.add(item)

    await db.flush()
    await db.refresh(invoice, ["items"])

    return invoice


async def update_invoice(
    db: AsyncSession,
    tenant_id: UUID,
    invoice_id: UUID,
    data: InvoiceUpdate,
) -> Invoice:
    """
    Update a draft invoice.

    Only draft invoices can be updated.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        invoice_id: Invoice UUID
        data: Update data

    Returns:
        Updated Invoice

    Raises:
        InvoiceNotFoundError: If invoice not found
        InvoiceNotDraftError: If invoice is not in draft status
    """
    invoice = await get_invoice_by_id(db, tenant_id, invoice_id)

    if not invoice:
        raise InvoiceNotFoundError(invoice_id)

    if invoice.status != InvoiceStatus.DRAFT:
        raise InvoiceNotDraftError(invoice_id, invoice.status)

    # Update fields that are provided
    update_data = data.model_dump(exclude_unset=True, exclude={"items"})
    for field, value in update_data.items():
        if value is not None:
            setattr(invoice, field, value)

    # If items are provided, replace all items
    if data.items is not None:
        # Delete existing items
        for item in invoice.items:
            await db.delete(item)

        # Create new items
        for item_data in data.items:
            item = _create_invoice_item(invoice.id, item_data)
            db.add(item)

    await db.flush()
    await db.refresh(invoice, ["items"])

    return invoice


async def delete_invoice(
    db: AsyncSession,
    tenant_id: UUID,
    invoice_id: UUID,
) -> None:
    """
    Delete a draft invoice.

    Only draft invoices can be deleted.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        invoice_id: Invoice UUID

    Raises:
        InvoiceNotFoundError: If invoice not found
        InvoiceNotDraftError: If invoice is not in draft status
    """
    invoice = await get_invoice_by_id(db, tenant_id, invoice_id, with_items=False)

    if not invoice:
        raise InvoiceNotFoundError(invoice_id)

    if invoice.status != InvoiceStatus.DRAFT:
        raise InvoiceNotDraftError(invoice_id, invoice.status)

    await db.delete(invoice)
    await db.flush()


async def submit_invoice(
    db: AsyncSession,
    tenant_id: UUID,
    invoice_id: UUID,
    fbr_service: FBRService,
) -> Invoice:
    """
    Submit an invoice to FBR.
    
    1. Verify invoice exists and is DRAFT.
    2. Call FBRService to submit.
    3. Update Invoice status based on outcome.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        invoice_id: Invoice UUID
        
    Returns:
        Updated Invoice
        
    Raises:
        InvoiceNotFoundError: If invoice not found
        InvoiceNotDraftError: If invoice is not in draft status
    """
    invoice = await get_invoice_by_id(db, tenant_id, invoice_id)
    
    if not invoice:
        raise InvoiceNotFoundError(invoice_id)
        
    if invoice.status != InvoiceStatus.DRAFT:
        raise InvoiceNotDraftError(invoice_id, invoice.status)
        
    # Submit to FBR
    response = await fbr_service.submit_invoice(invoice, db)
    
    # Check outcome
    is_success = "error" not in response
    
    if is_success:
        invoice.status = InvoiceStatus.SUBMITTED
        invoice.submitted_at = datetime.now(timezone.utc)
    else:
        # Mark as FAILED provides immediate feedback.
        invoice.status = InvoiceStatus.FAILED
    
    await db.commit()
    await db.refresh(invoice)
    
    return invoice


# =============================================================================
# Suggest Next RefNo
# =============================================================================


async def get_suggest_next_ref_no(
    db: AsyncSession,
    tenant_id: UUID,
) -> tuple[str | None, str | None]:
    """
    Get suggested next invoiceRefNo based on last submitted invoice.

    Args:
        db: Database session
        tenant_id: Tenant UUID

    Returns:
        Tuple of (suggested_ref_no, last_ref_no)
    """
    # Get the last successfully submitted invoice
    result = await db.execute(
        select(Invoice)
        .where(
            and_(
                Invoice.tenant_id == tenant_id,
                Invoice.status == InvoiceStatus.SUBMITTED,
            )
        )
        .order_by(Invoice.submitted_at.desc())
        .limit(1)
    )
    last_invoice = result.scalar_one_or_none()

    if not last_invoice:
        return None, None

    last_ref = last_invoice.invoice_ref_no
    suggested = suggest_next_ref_no(last_ref)

    return suggested, last_ref


# =============================================================================
# Helper Functions
# =============================================================================


def _create_invoice_item(invoice_id: UUID, data: InvoiceItemCreate) -> InvoiceItem:
    """Create an InvoiceItem from schema data."""
    return InvoiceItem(
        invoice_id=invoice_id,
        hs_code=data.hs_code,
        product_description=data.product_description,
        rate=data.rate,
        uom=data.uom,
        quantity=data.quantity,
        total_values=data.total_values,
        value_sales_excluding_st=data.value_sales_excluding_st,
        fixed_notified_value=data.fixed_notified_value,
        sales_tax_applicable=data.sales_tax_applicable,
        sales_tax_withheld=data.sales_tax_withheld,
        extra_tax=data.extra_tax,
        further_tax=data.further_tax,
        sro_schedule_no=data.sro_schedule_no,
        fed_payable=data.fed_payable,
        discount=data.discount,
        sale_type=data.sale_type,
        sro_item_serial_no=data.sro_item_serial_no,
    )
