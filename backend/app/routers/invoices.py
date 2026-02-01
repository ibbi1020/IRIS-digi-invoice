"""
Invoice router - CRUD endpoints for invoices.

All endpoints require authentication and are tenant-scoped.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import CurrentUserDep, DbSession
from app.models import InvoiceStatus, InvoiceType
from app.schemas.common import PaginationParams
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceStatusEnum,
    InvoiceSummaryResponse,
    InvoiceTypeEnum,
    InvoiceUpdate,
    SuggestRefNoResponse,
)
from app.services import invoice_service
from app.services.invoice_service import (
    InvoiceNotDraftError,
    InvoiceNotFoundError,
    InvoiceRefNoBlockedError,
    InvoiceRefNoExistsError,
    ReferencedInvoiceNotFoundError,
)

router = APIRouter(prefix="/invoices", tags=["Invoices"])


# =============================================================================
# Helper Functions
# =============================================================================


def _invoice_to_response(invoice) -> InvoiceResponse:
    """Convert Invoice model to InvoiceResponse schema."""
    from app.schemas.invoice import InvoiceItemResponse

    return InvoiceResponse(
        id=invoice.id,
        tenant_id=invoice.tenant_id,
        invoice_ref_no=invoice.invoice_ref_no,
        invoice_type=InvoiceTypeEnum(invoice.invoice_type.value),
        invoice_date=invoice.invoice_date,
        buyer_ntn_cnic=invoice.buyer_ntn_cnic,
        buyer_business_name=invoice.buyer_business_name,
        buyer_province=invoice.buyer_province,
        buyer_address=invoice.buyer_address,
        buyer_registration_type=invoice.buyer_registration_type,
        scenario_id=invoice.scenario_id,
        referenced_invoice_ref_no=(
            invoice.referenced_invoice.invoice_ref_no
            if invoice.referenced_invoice
            else None
        ),
        status=InvoiceStatusEnum(invoice.status.value),
        submitted_at=invoice.submitted_at,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        items=[
            InvoiceItemResponse(
                id=item.id,
                hs_code=item.hs_code,
                product_description=item.product_description,
                rate=item.rate,
                uom=item.uom,
                quantity=item.quantity,
                total_values=item.total_values,
                value_sales_excluding_st=item.value_sales_excluding_st,
                fixed_notified_value=item.fixed_notified_value,
                sales_tax_applicable=item.sales_tax_applicable,
                sales_tax_withheld=item.sales_tax_withheld,
                extra_tax=item.extra_tax,
                further_tax=item.further_tax,
                sro_schedule_no=item.sro_schedule_no,
                fed_payable=item.fed_payable,
                discount=item.discount,
                sale_type=item.sale_type,
                sro_item_serial_no=item.sro_item_serial_no,
            )
            for item in invoice.items
        ],
    )


def _invoice_to_summary(invoice) -> InvoiceSummaryResponse:
    """Convert Invoice model to InvoiceSummaryResponse schema."""
    return InvoiceSummaryResponse(
        id=invoice.id,
        invoice_ref_no=invoice.invoice_ref_no,
        invoice_type=InvoiceTypeEnum(invoice.invoice_type.value),
        invoice_date=invoice.invoice_date,
        buyer_business_name=invoice.buyer_business_name,
        status=InvoiceStatusEnum(invoice.status.value),
        item_count=len(invoice.items) if invoice.items else 0,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "",
    response_model=InvoiceListResponse,
    summary="List invoices",
    description="Get paginated list of invoices for the current tenant.",
)
async def list_invoices(
    current_user: CurrentUserDep,
    db: DbSession,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: InvoiceStatusEnum | None = Query(default=None, description="Filter by status"),
    type: InvoiceTypeEnum | None = Query(default=None, description="Filter by type"),
) -> InvoiceListResponse:
    """
    List all invoices for the authenticated user's tenant.

    Supports filtering by status and type, with pagination.
    """
    pagination = PaginationParams(page=page, page_size=page_size)

    # Convert enum to model enum if provided
    status_filter = InvoiceStatus(status.value) if status else None
    type_filter = InvoiceType(type.value) if type else None

    invoices, total = await invoice_service.list_invoices(
        db,
        current_user.tenant.id,
        pagination,
        status_filter=status_filter,
        type_filter=type_filter,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return InvoiceListResponse(
        items=[_invoice_to_summary(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invoice",
    description="Create a new draft invoice with line items.",
)
async def create_invoice(
    current_user: CurrentUserDep,
    db: DbSession,
    data: InvoiceCreate,
) -> InvoiceResponse:
    """
    Create a new draft invoice.

    - Invoice reference number must be unique per tenant
    - At least 1 line item is required
    - Debit/Credit notes must reference an existing submitted Sales Invoice
    """
    try:
        invoice = await invoice_service.create_invoice(
            db,
            current_user.tenant,
            data,
        )
        return _invoice_to_response(invoice)
    except InvoiceRefNoExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except InvoiceRefNoBlockedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ReferencedInvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/suggest-ref",
    response_model=SuggestRefNoResponse,
    summary="Suggest next invoice reference",
    description="Get suggested next invoiceRefNo based on last submitted invoice.",
)
async def suggest_ref_no(
    current_user: CurrentUserDep,
    db: DbSession,
) -> SuggestRefNoResponse:
    """
    Get a suggested next invoiceRefNo.

    Based on the last successfully submitted invoice:
    - If it has trailing digits, increment by 1 (preserving leading zeros)
    - If no trailing digits, no suggestion is provided
    """
    suggested, last_ref = await invoice_service.get_suggest_next_ref_no(
        db,
        current_user.tenant.id,
    )
    return SuggestRefNoResponse(
        suggested_ref_no=suggested,
        last_ref_no=last_ref,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice",
    description="Get a single invoice by ID with all line items.",
)
async def get_invoice(
    current_user: CurrentUserDep,
    db: DbSession,
    invoice_id: UUID,
) -> InvoiceResponse:
    """
    Get invoice details by ID.

    Returns the invoice with all line items.
    """
    invoice = await invoice_service.get_invoice_by_id(
        db,
        current_user.tenant.id,
        invoice_id,
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice not found: {invoice_id}",
        )

    return _invoice_to_response(invoice)


@router.put(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Update invoice",
    description="Update a draft invoice. Only draft invoices can be modified.",
)
async def update_invoice(
    current_user: CurrentUserDep,
    db: DbSession,
    invoice_id: UUID,
    data: InvoiceUpdate,
) -> InvoiceResponse:
    """
    Update a draft invoice.

    - Only draft invoices can be updated
    - If items are provided, they replace all existing items
    """
    try:
        invoice = await invoice_service.update_invoice(
            db,
            current_user.tenant.id,
            invoice_id,
            data,
        )
        return _invoice_to_response(invoice)
    except InvoiceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice not found: {invoice_id}",
        )
    except InvoiceNotDraftError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete invoice",
    description="Delete a draft invoice. Only draft invoices can be deleted.",
)
async def delete_invoice(
    current_user: CurrentUserDep,
    db: DbSession,
    invoice_id: UUID,
) -> None:
    """
    Delete a draft invoice.

    Only draft invoices can be deleted. Submitted, failed, or unknown
    invoices cannot be deleted for audit purposes.
    """
    try:
        await invoice_service.delete_invoice(
            db,
            current_user.tenant.id,
            invoice_id,
        )
    except InvoiceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice not found: {invoice_id}",
        )
    except InvoiceNotDraftError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{invoice_id}/submit",
    response_model=InvoiceResponse,
    summary="Submit invoice to FBR",
    description="Submit a draft invoice to FBR IRIS system.",
)
async def submit_invoice(
    current_user: CurrentUserDep,
    db: DbSession,
    invoice_id: UUID,
) -> InvoiceResponse:
    """
    Submit invoice to FBR.
    
    - Transition status from DRAFT -> SUBMITTED (or FAILED)
    - Logs submission attempt
    """
    try:
        invoice = await invoice_service.submit_invoice(
            db,
            current_user.tenant.id,
            invoice_id,
        )
        return _invoice_to_response(invoice)
    except InvoiceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice not found: {invoice_id}",
        )
    except InvoiceNotDraftError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
