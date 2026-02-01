import pytest
from httpx import AsyncClient

# Test credentials (from scripts/seed_user.py)
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "password123"

@pytest.mark.asyncio
async def test_invoice_lifecycle(client: AsyncClient):
    # 1. Login
    login_payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    login_response = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Invoice
    import uuid
    random_ref = f"INV-TEST-{uuid.uuid4().hex[:8].upper()}"
    
    invoice_payload = {
        "invoice_ref_no": random_ref,
        "invoice_date": "2023-10-26",
        "description": "Integration Test Invoice", # Note: description is not in InvoiceBase, check if it's there? Wait.
        # Checking InvoiceBase: invoice_ref_no, invoice_type, invoice_date, buyer_ntn_cnic, buyer_business_name, ...
        # There is NO generic 'description' field in InvoiceBase! 
        # But maybe I need validation? 
        "invoice_type": "Sale Invoice",
        "buyer_business_name": "Test Buyer",
        "buyer_ntn_cnic": "9999999999999", # 13 digits, no dashes or dashes allowed? Validation says digits only if stripped.
        "buyer_province": "Punjab",
        "buyer_address": "123 Test St",
        "buyer_registration_type": "Registered",
        "items": [
            {
                "hs_code": "0000.0000",
                "product_description": "Test Widget",
                "quantity": 2.0,
                "uom": "PCS",
                "rate": "10%",
                "total_values": 220.0,
                "value_sales_excluding_st": 200.0,
                "sales_tax_applicable": 20.0,
            }
        ]
    }
    
    # Note: 'description' was in my previous test payload but it seems it's not in the schema?
    # Let's remove valid fields only.
    
    create_response = await client.post("/api/v1/invoices", json=invoice_payload, headers=headers)
    assert create_response.status_code == 201, f"Create failed: {create_response.text}"
    invoice_data = create_response.json()
    invoice_id = invoice_data["id"]
    assert invoice_data["invoice_ref_no"] == random_ref
    assert invoice_data["item_count"] == 1
    
    # 3. Get Invoice
    get_response = await client.get(f"/api/v1/invoices/{invoice_id}", headers=headers)
    assert get_response.status_code == 200, f"Get failed: {get_response.text}"
    assert get_response.json()["id"] == invoice_id
    
    # 4. List Invoices
    list_response = await client.get("/api/v1/invoices", headers=headers)
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert any(i["id"] == invoice_id for i in items), "Created invoice not found in list"
    
    # 5. Update Invoice
    update_payload = {
        "buyer_business_name": "Updated Buyer Name",
        "items": [
             {
                "hs_code": "0000.0000",
                "product_description": "Test Widget",
                "quantity": 3.0,
                "uom": "PCS",
                "rate": "10%",
                "total_values": 330.0,
                "value_sales_excluding_st": 300.0,
                "sales_tax_applicable": 30.0,
            }
        ]
    }
    
    put_response = await client.put(f"/api/v1/invoices/{invoice_id}", json=update_payload, headers=headers)
    assert put_response.status_code == 200, f"Update failed: {put_response.text}"
    updated_data = put_response.json()
    assert updated_data["buyer_business_name"] == "Updated Buyer Name"
    # API wrapper for DecimalField might enforce 2 decimal places in serialization or DB default
    assert float(updated_data["items"][0]["quantity"]) == 3.0
    
    # 6. Delete Invoice
    delete_response = await client.delete(f"/api/v1/invoices/{invoice_id}", headers=headers)
    assert delete_response.status_code == 204
    
    # 7. Verify Deletion
    get_again = await client.get(f"/api/v1/invoices/{invoice_id}", headers=headers)
    assert get_again.status_code == 404
