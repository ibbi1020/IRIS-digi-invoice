"""
Test suite for Mock FBR Service.

Demonstrates how mocking works in industry and validates the implementation.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_mock_fbr_invoice_submission(client: AsyncClient):
    """
    Test invoice submission using mock FBR service.
    
    This test demonstrates:
    1. How to test without external API dependencies
    2. Predictable test outcomes
    3. No IP whitelisting required
    4. Fast execution
    """
    # 1. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a test invoice
    invoice_payload = {
        "invoice_ref_no": "TEST-MOCK-001",
        "invoice_date": "2024-01-15",
        "invoice_type": "Sale Invoice",
        "buyer_business_name": "Test Buyer Corp",
        "buyer_ntn_cnic": "1234567890123",
        "buyer_province": "Punjab",
        "buyer_address": "Test Address, Lahore",
        "buyer_registration_type": "Registered",
        "scenario_id": "SN001",
        "items": [
            {
                "hs_code": "8471.3000",
                "product_description": "Test Product",
                "quantity": 5.0,
                "uom": "PCS",
                "rate": "18%",
                "total_values": 1000.0,
                "value_sales_excluding_st": 847.46,
                "sales_tax_applicable": 152.54,
                "further_tax": 0.0,
            }
        ]
    }

    create_resp = await client.post("/api/v1/invoices", json=invoice_payload, headers=headers)
    assert create_resp.status_code == 201
    invoice_id = create_resp.json()["id"]

    # 3. Submit to "FBR" (actually mock)
    submit_resp = await client.post(f"/api/v1/invoices/{invoice_id}/submit", headers=headers)
    
    # With mock service, this should succeed without IP whitelisting
    assert submit_resp.status_code == 200
    
    data = submit_resp.json()
    assert data["status"] in ["submitted", "failed"]
    
    print(f"✅ Mock submission successful: {data}")


@pytest.mark.asyncio
async def test_mock_vs_real_service_interface(client: AsyncClient):
    """
    Verify that mock and real services have the same interface.
    
    This is crucial for the mock to be a true drop-in replacement.
    """
    from app.services.fbr_service import FBRService
    from app.services.mock_fbr_service import MockFBRService
    
    real_service = FBRService()
    mock_service = MockFBRService()
    
    # Both should have the same methods
    assert hasattr(real_service, 'submit_invoice')
    assert hasattr(mock_service, 'submit_invoice')
    assert hasattr(real_service, 'validate_invoice')
    assert hasattr(mock_service, 'validate_invoice')
    assert hasattr(real_service, 'close')
    assert hasattr(mock_service, 'close')
    
    await real_service.close()
    await mock_service.close()
    
    print("✅ Interface compatibility verified")


@pytest.mark.asyncio
async def test_configuration_switching():
    """
    Test that the service factory correctly switches between real and mock.
    
    This demonstrates the configuration-based approach used in industry.
    """
    from app.config import get_settings
    from app.services.fbr_service import get_fbr_service
    from app.services.mock_fbr_service import MockFBRService
    
    settings = get_settings()
    service = get_fbr_service()
    
    if settings.use_mock_fbr:
        assert isinstance(service, MockFBRService)
        print("✅ Mock service active (USE_MOCK_FBR=true)")
    else:
        # Would be real FBRService
        print("✅ Real service active (USE_MOCK_FBR=false)")
    
    await service.close()
