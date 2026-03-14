"""
Mock FBR Service for Development and Testing.

This service simulates FBR API responses without making actual HTTP calls.
Used when USE_MOCK_FBR=true in environment configuration.

Industry Best Practice:
- Allows development without external API dependencies
- Enables testing of error scenarios
- No IP whitelisting required
- Faster test execution
- Predictable responses
"""

import uuid
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.submission_attempt import SubmissionAttempt, SubmissionOutcome

logger = structlog.get_logger()


class MockFBRService:
    """Mock implementation of FBR service for development/testing."""

    def __init__(self):
        """Initialize mock service."""
        logger.info("mock_fbr_service_initialized", mode="DEVELOPMENT")

    async def close(self):
        """Close method for compatibility (no-op for mock)."""
        pass

    def _build_payload(self, invoice: Invoice) -> dict[str, Any]:
        """
        Build FBR payload (same as real service).
        Kept for compatibility and testing payload construction.
        """
        items = []
        for item in invoice.items:
            items.append({
                "ItemCode": item.hs_code,
                "ItemName": item.product_description,
                "PCTCode": item.hs_code.replace(".", "") if item.hs_code else "",
                "Quantity": float(item.quantity),
                "TaxRate": float(item.rate.replace("%", "").strip()) if item.rate else 0.0,
                "SaleValue": float(item.value_sales_excluding_st),
                "TotalAmount": float(item.total_values),
                "TaxCharged": float(item.sales_tax_applicable),
                "FurtherTax": float(item.further_tax),
                "ExtraTax": float(item.extra_tax) if item.extra_tax else 0.0,
                "InvoiceType": "1",
                "UOM": item.uom,
                "Discount": float(item.discount),
                "FinanceAct": item.sro_schedule_no or "",
            })

        payload = {
            "InvoiceNumber": invoice.invoice_ref_no,
            "POSID": 123456,
            "USIN": invoice.invoice_ref_no,
            "DateTime": invoice.invoice_date.strftime("%Y-%m-%d") + " 00:00:00",
            "BuyerName": invoice.buyer_business_name,
            "BuyerNTN": invoice.buyer_ntn_cnic.replace("-", ""),
            "BuyerCNIC": invoice.buyer_ntn_cnic.replace("-", "") if len(invoice.buyer_ntn_cnic) > 9 else "",
            "BuyerType": "1" if invoice.buyer_registration_type.value == "Registered" else "2",
            "TotalSaleValue": sum(i["SaleValue"] for i in items),
            "TotalTaxCharged": sum(i["TaxCharged"] for i in items),
            "TotalBillAmount": sum(i["TotalAmount"] for i in items),
            "TotalQuantity": sum(i["Quantity"] for i in items),
            "Items": items,
            "SellerNTN": invoice.tenant.seller_ntn.replace("-", "") if invoice.tenant and invoice.tenant.seller_ntn else "",
        }

        return payload

    async def submit_invoice(self, invoice: Invoice, db: Session) -> dict[str, Any]:
        """
        Mock invoice submission.
        
        Returns realistic FBR responses based on invoice data.
        Simulates different scenarios for testing.
        """
        payload = self._build_payload(invoice)
        
        logger.info(
            "mock_fbr_submission",
            ref_no=invoice.invoice_ref_no,
            scenario=invoice.scenario_id,
            mode="MOCK"
        )

        print(f"\n[MOCK] Simulating FBR submission for {invoice.invoice_ref_no}")
        print(f"[MOCK] Scenario: {invoice.scenario_id}")
        print(f"[MOCK] Payload constructed: {len(payload)} fields")

        # Create submission attempt record
        attempt_id = uuid.uuid4()
        attempt = SubmissionAttempt(
            id=attempt_id,
            invoice_id=invoice.id,
            attempt_number=1,
            endpoint="MOCK_FBR_ENDPOINT",
            outcome=SubmissionOutcome.SUCCESS,
            diagnostic_id=attempt_id.hex[:8],
            http_status=200,
            response_summary="Mock successful submission",
            response_time_ms=150,  # Simulated response time
        )
        db.add(attempt)
        await db.commit()

        # Simulate different responses based on scenario
        # This allows testing various FBR response scenarios
        
        # Success response (most common)
        mock_response = {
            "Code": 100,
            "Message": "Invoice submitted successfully",
            "InvoiceNumber": invoice.invoice_ref_no,
            "USIN": invoice.invoice_ref_no,
            "FBRInvoiceNumber": f"FBR-{uuid.uuid4().hex[:12].upper()}",
            "Timestamp": datetime.utcnow().isoformat(),
            "Status": "Accepted",
        }

        # Simulate validation errors for specific test scenarios
        if invoice.scenario_id == "ERROR_TEST":
            mock_response = {
                "Code": 400,
                "Message": "Validation Error",
                "Errors": [
                    {"Field": "BuyerNTN", "Error": "Invalid NTN format"}
                ]
            }
        elif invoice.scenario_id == "TIMEOUT_TEST":
            # Simulate timeout scenario
            attempt.outcome = SubmissionOutcome.TIMEOUT
            attempt.response_summary = "Simulated timeout"
            await db.commit()
            return {"error": "Timeout", "detail": "Simulated timeout for testing"}

        logger.info(
            "mock_fbr_response",
            ref_no=invoice.invoice_ref_no,
            code=mock_response.get("Code"),
            status=mock_response.get("Status")
        )

        return mock_response

    async def validate_invoice(self, invoice: Invoice, db: Session) -> dict[str, Any]:
        """
        Mock invoice validation.
        
        Simulates FBR validation endpoint response.
        """
        payload = self._build_payload(invoice)
        
        logger.info(
            "mock_fbr_validation",
            ref_no=invoice.invoice_ref_no,
            mode="MOCK"
        )

        print(f"\n[MOCK] Simulating FBR validation for {invoice.invoice_ref_no}")

        # Mock validation response
        mock_response = {
            "dated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "validationResponse": {
                "statusCode": "00",
                "status": "Valid",
                "InvoiceNumber": invoice.invoice_ref_no,
                "VerificationStatus": "Verified",
                "TaxAmount": float(sum(item.sales_tax_applicable for item in invoice.items)),
                "TotalAmount": float(sum(item.total_values for item in invoice.items)),
            }
        }

        return mock_response


# Global instance
_mock_fbr_service = None


def get_mock_fbr_service() -> MockFBRService:
    """Get or create mock FBR service instance."""
    global _mock_fbr_service
    if _mock_fbr_service is None:
        _mock_fbr_service = MockFBRService()
    return _mock_fbr_service
