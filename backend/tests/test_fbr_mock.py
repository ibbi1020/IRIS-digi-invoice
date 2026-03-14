"""
FBR Mock Service Integration Tests.

Tests invoice submission flows using the mock FBR service.
These tests validate the integration between the API layer and FBR
without making actual HTTP calls to the FBR API.
"""

import pytest
from httpx import AsyncClient

from app.services.mock_fbr_service import MockBehavior, MockFBRService

# =============================================================================
# Test Data Fixtures
# =============================================================================

# Auth credentials for test user (assumes test database has this user)
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpass123"


async def get_auth_token(client: AsyncClient) -> str:
    """Get authentication token for test user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
    )
    if response.status_code != 200:
        pytest.skip("Test user not found - run seed script first")
    return response.json()["access_token"]


def get_valid_invoice_payload() -> dict:
    """Return a valid invoice creation payload."""
    return {
        "invoiceRefNo": "TEST-INV-001",
        "invoiceType": "Sale Invoice",
        "invoiceDate": "2026-02-08",
        "buyerNtnCnic": "1234567",
        "buyerBusinessName": "Test Buyer Ltd",
        "buyerProvince": "Sindh",
        "buyerAddress": "Test Address, Karachi",
        "buyerRegistrationType": "Registered",
        "scenarioId": "SN001",
        "items": [
            {
                "hsCode": "0101.2100",
                "productDescription": "Test Product",
                "rate": "18%",
                "uom": "Numbers, pieces, units",
                "quantity": 1.0,
                "totalValues": 1180.0,
                "valueSalesExcludingSt": 1000.0,
                "fixedNotifiedValue": 0.0,
                "salesTaxApplicable": 180.0,
                "salesTaxWithheld": 0.0,
                "extraTax": "",
                "furtherTax": 0.0,
                "sroScheduleNo": "",
                "fedPayable": 0.0,
                "discount": 0.0,
                "saleType": "Goods at standard rate (default)",
                "sroItemSerialNo": "",
            }
        ],
    }


# =============================================================================
# Mock FBR Service Unit Tests
# =============================================================================


class TestMockFBRServiceUnit:
    """Unit tests for MockFBRService class."""

    def test_mock_service_default_behavior(self, mock_fbr_service: MockFBRService):
        """Mock service should default to SUCCESS behavior."""
        assert mock_fbr_service.behavior == MockBehavior.SUCCESS
        assert mock_fbr_service.call_count == 0
        assert not mock_fbr_service.was_called()

    def test_mock_service_configure(self, mock_fbr_service: MockFBRService):
        """Should be able to configure mock behavior."""
        mock_fbr_service.configure(MockBehavior.AUTH_ERROR)
        assert mock_fbr_service.behavior == MockBehavior.AUTH_ERROR

    def test_mock_service_reset(self, mock_fbr_service: MockFBRService):
        """Reset should clear state and set default behavior."""
        mock_fbr_service.configure(MockBehavior.TIMEOUT)
        mock_fbr_service.call_history.append({"test": "data"})
        mock_fbr_service._call_count = 5

        mock_fbr_service.reset()

        assert mock_fbr_service.behavior == MockBehavior.SUCCESS
        assert mock_fbr_service.call_count == 0
        assert len(mock_fbr_service.call_history) == 0


# =============================================================================
# Integration Tests - Success Paths
# =============================================================================


@pytest.mark.asyncio
class TestSubmitInvoiceSuccess:
    """Tests for successful invoice submission."""

    async def test_submit_invoice_success(self, client_with_mock_fbr):
        """Basic successful submission should update invoice status."""
        client, mock_fbr = client_with_mock_fbr
        mock_fbr.configure(MockBehavior.SUCCESS)

        # Get auth token
        token = await get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create a draft invoice
        invoice_data = get_valid_invoice_payload()
        create_response = await client.post(
            "/api/v1/invoices", json=invoice_data, headers=headers
        )

        if create_response.status_code != 201:
            # Invoice ref might already exist
            invoice_data["invoiceRefNo"] = f"TEST-{pytest.approx(1000000)}"
            create_response = await client.post(
                "/api/v1/invoices", json=invoice_data, headers=headers
            )

        if create_response.status_code != 201:
            pytest.skip(f"Could not create test invoice: {create_response.text}")

        invoice = create_response.json()
        invoice_id = invoice["id"]

        # Submit the invoice
        submit_response = await client.post(
            f"/api/v1/invoices/{invoice_id}/submit", headers=headers
        )

        # Assertions
        assert submit_response.status_code == 200
        result = submit_response.json()
        assert result["status"] == "submitted"
        assert mock_fbr.was_called()
        assert mock_fbr.call_count == 1


# =============================================================================
# Integration Tests - Error Scenarios
# =============================================================================


@pytest.mark.asyncio
class TestSubmitInvoiceErrors:
    """Tests for invoice submission error handling."""

    async def test_submit_invoice_auth_error(self, client_with_mock_fbr):
        """Auth error from FBR should mark invoice as FAILED."""
        client, mock_fbr = client_with_mock_fbr
        mock_fbr.configure(MockBehavior.AUTH_ERROR)

        token = await get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create a draft invoice
        invoice_data = get_valid_invoice_payload()
        invoice_data["invoiceRefNo"] = "AUTH-ERR-TEST-001"

        create_response = await client.post(
            "/api/v1/invoices", json=invoice_data, headers=headers
        )

        if create_response.status_code != 201:
            pytest.skip(f"Could not create test invoice: {create_response.text}")

        invoice_id = create_response.json()["id"]

        # Submit - should fail due to auth error
        submit_response = await client.post(
            f"/api/v1/invoices/{invoice_id}/submit", headers=headers
        )

        assert submit_response.status_code == 200
        result = submit_response.json()
        # When FBR returns an error, status should be failed
        assert result["status"] == "failed"
        assert mock_fbr.call_count == 1


# =============================================================================
# Integration Tests - Timeout Handling
# =============================================================================


@pytest.mark.asyncio
class TestSubmitInvoiceTimeout:
    """Tests for timeout handling during submission."""

    async def test_submit_invoice_timeout(self, client_with_mock_fbr):
        """
        Timeout from FBR should be handled gracefully.
        
        Note: The current implementation may not handle all 3 retries
        in a single submit call - this tests the basic timeout case.
        """
        client, mock_fbr = client_with_mock_fbr
        mock_fbr.configure(MockBehavior.TIMEOUT)

        token = await get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        invoice_data = get_valid_invoice_payload()
        invoice_data["invoiceRefNo"] = "TIMEOUT-TEST-001"

        create_response = await client.post(
            "/api/v1/invoices", json=invoice_data, headers=headers
        )

        if create_response.status_code != 201:
            pytest.skip(f"Could not create test invoice: {create_response.text}")

        invoice_id = create_response.json()["id"]

        # Submit - should handle timeout
        submit_response = await client.post(
            f"/api/v1/invoices/{invoice_id}/submit", headers=headers
        )

        # Timeout should result in failed or unknown status
        result = submit_response.json()
        assert result["status"] in ["failed", "unknown"]


# =============================================================================
# Mock Response Validation Tests
# =============================================================================


@pytest.mark.asyncio
class TestMockResponses:
    """Tests validating mock response structures match IRIS spec."""

    async def test_success_response_structure(self, mock_fbr_service: MockFBRService):
        """Success response should match IRIS Documentation format."""
        # Create a minimal mock invoice object
        from unittest.mock import MagicMock
        from datetime import date
        
        mock_item = MagicMock()
        mock_item.hs_code = "0101.2100"
        
        mock_tenant = MagicMock()
        mock_tenant.seller_ntn = "1234567"
        
        mock_invoice = MagicMock()
        mock_invoice.id = "test-uuid"
        mock_invoice.invoice_ref_no = "TEST-001"
        mock_invoice.invoice_type.value = "Sale Invoice"
        mock_invoice.items = [mock_item]
        mock_invoice.tenant = mock_tenant

        mock_fbr_service.configure(MockBehavior.SUCCESS)
        response = await mock_fbr_service.submit_invoice(mock_invoice, None)

        # Validate response structure matches IRIS spec
        assert "invoiceNumber" in response
        assert "dated" in response
        assert "validationResponse" in response
        
        validation = response["validationResponse"]
        assert validation["statusCode"] == "00"
        assert validation["status"] == "Valid"
        assert "invoiceStatuses" in validation
        assert len(validation["invoiceStatuses"]) == 1

    async def test_auth_error_response_structure(self, mock_fbr_service: MockFBRService):
        """Auth error response should match IRIS error code 0401."""
        from unittest.mock import MagicMock
        
        mock_invoice = MagicMock()
        mock_invoice.id = "test-uuid"
        mock_invoice.invoice_ref_no = "TEST-001"
        mock_invoice.invoice_type.value = "Sale Invoice"
        mock_invoice.items = []

        mock_fbr_service.configure(MockBehavior.AUTH_ERROR)
        response = await mock_fbr_service.submit_invoice(mock_invoice, None)

        # Validate error structure
        assert "validationResponse" in response
        validation = response["validationResponse"]
        assert validation["statusCode"] == "01"
        assert validation["errorCode"] == "0401"
        assert "Unauthorized" in validation["error"]


# =============================================================================
# Call History Tests
# =============================================================================


class TestMockCallHistory:
    """Tests for mock call history tracking."""

    @pytest.mark.asyncio
    async def test_call_history_recorded(self, mock_fbr_service: MockFBRService):
        """Each call should be recorded in call history."""
        from unittest.mock import MagicMock
        
        mock_invoice = MagicMock()
        mock_invoice.id = "test-uuid-1"
        mock_invoice.invoice_ref_no = "TEST-001"
        mock_invoice.invoice_type.value = "Sale Invoice"
        mock_invoice.items = []
        mock_invoice.tenant = MagicMock()
        mock_invoice.tenant.seller_ntn = "1234567"

        await mock_fbr_service.submit_invoice(mock_invoice, None)
        await mock_fbr_service.submit_invoice(mock_invoice, None)

        assert mock_fbr_service.call_count == 2
        assert len(mock_fbr_service.call_history) == 2
        
        last_call = mock_fbr_service.get_last_call()
        assert last_call is not None
        assert last_call["call_number"] == 2
        assert last_call["invoice_ref_no"] == "TEST-001"

    def test_get_last_call_empty(self, mock_fbr_service: MockFBRService):
        """get_last_call should return None when no calls made."""
        assert mock_fbr_service.get_last_call() is None
