"""
Mock FBR Service for testing purposes.

This module provides a configurable mock implementation of the FBR service
that can simulate various response scenarios (success, validation errors,
auth errors, timeouts, etc.) for integration testing.

Usage:
    mock_service = MockFBRService()
    mock_service.configure(MockBehavior.SUCCESS)
    response = await mock_service.submit_invoice(invoice, db)
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol

import httpx
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class MockBehavior(str, enum.Enum):
    """Configurable behaviors for the mock FBR service."""
    
    SUCCESS = "success"
    VALIDATION_ERROR_HEADER = "validation_error_header"  # Error at invoice level
    VALIDATION_ERROR_ITEM = "validation_error_item"  # Error at item level
    AUTH_ERROR = "auth_error"  # Error 0401 - invalid seller NTN
    INVALID_BUYER_NTN = "invalid_buyer_ntn"  # Error 0002
    MISSING_HS_CODE = "missing_hs_code"  # Error 0052
    MISSING_RATE = "missing_rate"  # Error 0046
    SELF_INVOICING = "self_invoicing"  # Error 0058
    DUPLICATE_INVOICE = "duplicate_invoice"  # Error 0064
    TIMEOUT = "timeout"  # Simulates httpx.TimeoutException
    NETWORK_ERROR = "network_error"  # Simulates httpx.ConnectError
    PARTIAL_TIMEOUT = "partial_timeout"  # First call times out, second succeeds


class FBRServiceProtocol(Protocol):
    """Protocol defining the interface for FBR services."""
    
    async def submit_invoice(self, invoice: Invoice, db: Session) -> dict[str, Any]:
        """Submit an invoice to FBR and return the response."""
        ...


class MockFBRService:
    """
    Mock FBR service for testing.
    
    Can be configured to return various responses for testing different
    scenarios without making actual HTTP calls to the FBR API.
    """
    
    def __init__(self) -> None:
        self.behavior: MockBehavior = MockBehavior.SUCCESS
        self.call_history: list[dict[str, Any]] = []
        self._call_count: int = 0
        self._partial_timeout_threshold: int = 1  # Fail first N calls for partial timeout
    
    def configure(
        self,
        behavior: MockBehavior,
        *,
        partial_timeout_threshold: int = 1,
    ) -> None:
        """
        Configure the mock behavior.
        
        Args:
            behavior: The behavior to simulate
            partial_timeout_threshold: For PARTIAL_TIMEOUT, how many calls to fail before success
        """
        self.behavior = behavior
        self._partial_timeout_threshold = partial_timeout_threshold
    
    def reset(self) -> None:
        """Reset the mock state (clear call history and counter)."""
        self.call_history.clear()
        self._call_count = 0
        self.behavior = MockBehavior.SUCCESS
    
    async def submit_invoice(self, invoice: Invoice, db: Session) -> dict[str, Any]:
        """
        Simulate submitting an invoice to FBR.
        
        Records the call and returns a response based on configured behavior.
        
        Args:
            invoice: The invoice to submit
            db: Database session (not used in mock, kept for interface compatibility)
        
        Returns:
            A dict simulating the FBR API response
        
        Raises:
            httpx.TimeoutException: If behavior is TIMEOUT
            httpx.ConnectError: If behavior is NETWORK_ERROR
        """
        self._call_count += 1
        
        # Record the call for test assertions
        call_record = {
            "call_number": self._call_count,
            "invoice_id": str(invoice.id),
            "invoice_ref_no": invoice.invoice_ref_no,
            "invoice_type": invoice.invoice_type.value,
            "behavior": self.behavior.value,
            "timestamp": datetime.now().isoformat(),
        }
        self.call_history.append(call_record)
        
        # Generate response based on configured behavior
        return await self._generate_response(invoice)
    
    async def _generate_response(self, invoice: Invoice) -> dict[str, Any]:
        """Generate the appropriate response based on current behavior."""
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        match self.behavior:
            case MockBehavior.SUCCESS:
                return self._success_response(invoice, now)
            
            case MockBehavior.VALIDATION_ERROR_HEADER:
                return self._header_validation_error(now)
            
            case MockBehavior.VALIDATION_ERROR_ITEM:
                return self._item_validation_error(now)
            
            case MockBehavior.AUTH_ERROR:
                return self._auth_error(now)
            
            case MockBehavior.INVALID_BUYER_NTN:
                return self._invalid_buyer_ntn_error(now)
            
            case MockBehavior.MISSING_HS_CODE:
                return self._missing_hs_code_error(now)
            
            case MockBehavior.MISSING_RATE:
                return self._missing_rate_error(now)
            
            case MockBehavior.SELF_INVOICING:
                return self._self_invoicing_error(now)
            
            case MockBehavior.DUPLICATE_INVOICE:
                return self._duplicate_invoice_error(now)
            
            case MockBehavior.TIMEOUT:
                raise httpx.TimeoutException("Request timed out")
            
            case MockBehavior.NETWORK_ERROR:
                raise httpx.ConnectError("Connection refused")
            
            case MockBehavior.PARTIAL_TIMEOUT:
                if self._call_count <= self._partial_timeout_threshold:
                    raise httpx.TimeoutException("Request timed out")
                return self._success_response(invoice, now)
            
            case _:
                return self._success_response(invoice, now)
    
    def _generate_fbr_invoice_number(self, invoice: Invoice) -> str:
        """Generate a fake FBR invoice number in the official format."""
        # Format: {NTN}DI{timestamp_milliseconds}
        ntn = invoice.tenant.seller_ntn.replace("-", "") if invoice.tenant else "0000000"
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"{ntn}DI{timestamp}"
    
    def _success_response(self, invoice: Invoice, dated: str) -> dict[str, Any]:
        """Generate a successful FBR response."""
        fbr_invoice_no = self._generate_fbr_invoice_number(invoice)
        
        # Build item statuses
        invoice_statuses = []
        for i, item in enumerate(invoice.items, start=1):
            invoice_statuses.append({
                "itemSNo": str(i),
                "statusCode": "00",
                "status": "Valid",
                "invoiceNo": f"{fbr_invoice_no}-{i}",
                "errorCode": "",
                "error": "",
            })
        
        return {
            "invoiceNumber": fbr_invoice_no,
            "dated": dated,
            "validationResponse": {
                "statusCode": "00",
                "status": "Valid",
                "error": "",
                "invoiceStatuses": invoice_statuses,
            },
        }
    
    def _header_validation_error(self, dated: str) -> dict[str, Any]:
        """Generate a header-level validation error."""
        return {
            "dated": dated,
            "validationResponse": {
                "statusCode": "01",
                "status": "Invalid",
                "errorCode": "0052",
                "error": "Provide proper HS Code with invoice no. null",
                "invoiceStatuses": None,
            },
        }
    
    def _item_validation_error(self, dated: str) -> dict[str, Any]:
        """Generate an item-level validation error."""
        return {
            "dated": dated,
            "validationResponse": {
                "statusCode": "00",
                "status": "invalid",
                "error": "",
                "invoiceStatuses": [
                    {
                        "itemSNo": "1",
                        "statusCode": "01",
                        "status": "Invalid",
                        "invoiceNo": None,
                        "errorCode": "0046",
                        "error": "Provide rate.",
                    }
                ],
            },
        }
    
    def _auth_error(self, dated: str) -> dict[str, Any]:
        """Generate an auth error (invalid seller NTN/token)."""
        return {
            "dated": dated,
            "validationResponse": {
                "statusCode": "01",
                "status": "Invalid",
                "errorCode": "0401",
                "error": (
                    "Unauthorized access: Provided seller registration number is not "
                    "13 digits (CNIC) or 7 digits (NTN) or the authorized token does "
                    "not exist against seller registration number"
                ),
            },
        }
    
    def _invalid_buyer_ntn_error(self, dated: str) -> dict[str, Any]:
        """Generate an invalid buyer NTN error."""
        return {
            "dated": dated,
            "validationResponse": {
                "statusCode": "01",
                "status": "Invalid",
                "errorCode": "0002",
                "error": (
                    "Buyer Registration Number or NTN is not in proper format, "
                    "please provide buyer registration number in 13 digits or NTN in 7 or 9 digits"
                ),
            },
        }
    
    def _missing_hs_code_error(self, dated: str) -> dict[str, Any]:
        """Generate a missing HS code error."""
        return {
            "dated": dated,
            "validationResponse": {
                "statusCode": "01",
                "status": "Invalid",
                "errorCode": "0052",
                "error": "Please provide valid HS Code against invoice no: null",
                "invoiceStatuses": None,
            },
        }
    
    def _missing_rate_error(self, dated: str) -> dict[str, Any]:
        """Generate a missing rate error."""
        return {
            "dated": dated,
            "validationResponse": {
                "statusCode": "01",
                "status": "Invalid",
                "errorCode": "0046",
                "error": "Rate cannot be empty, please provide valid rate as per selected Sales Type.",
                "invoiceStatuses": None,
            },
        }
    
    def _self_invoicing_error(self, dated: str) -> dict[str, Any]:
        """Generate a self-invoicing error (buyer = seller)."""
        return {
            "dated": dated,
            "validationResponse": {
                "statusCode": "01",
                "status": "Invalid",
                "errorCode": "0058",
                "error": "Buyer and Seller Registration number are same, this type of invoice is not allowed",
            },
        }
    
    def _duplicate_invoice_error(self, dated: str) -> dict[str, Any]:
        """Generate a duplicate invoice (ref already exists) error."""
        return {
            "dated": dated,
            "validationResponse": {
                "statusCode": "01",
                "status": "Invalid",
                "errorCode": "0064",
                "error": "Reference invoice already exist.",
            },
        }
    
    # Helper methods for test assertions
    
    @property
    def call_count(self) -> int:
        """Return the number of times submit_invoice was called."""
        return self._call_count
    
    def was_called(self) -> bool:
        """Return True if submit_invoice was called at least once."""
        return self._call_count > 0
    
    def get_last_call(self) -> dict[str, Any] | None:
        """Return the most recent call record, or None if no calls."""
        return self.call_history[-1] if self.call_history else None


# Factory function for dependency injection
def get_mock_fbr_service() -> MockFBRService:
    """Create a new MockFBRService instance."""
    return MockFBRService()
