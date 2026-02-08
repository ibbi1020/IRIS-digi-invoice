"""
FBR (IRIS) Integration Service.

Handles submission of invoices to the FBR API.
"""

import asyncio
import uuid
from typing import Any

import httpx
import structlog
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.invoice import Invoice
from app.models.submission_attempt import SubmissionAttempt, SubmissionOutcome
from app.models.tenant import Tenant

logger = structlog.get_logger()
settings = get_settings()


class FBRService:
    """Service for interacting with FBR IRIS 2.0 API."""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.fbr_auth_token}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=float(settings.fbr_timeout_seconds),
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _build_payload(self, invoice: Invoice) -> dict[str, Any]:
        """
        Construct FBR JSON payload from Invoice model.
        
        Maps internal model fields to official IRIS API expected keys.
        Reference: IRIS Documentation.md Section 4.1
        """
        # Build items array per IRIS spec
        items = []
        for item in invoice.items:
            item_payload = {
                "hsCode": item.hs_code,
                "productDescription": item.product_description,
                "rate": item.rate,  # e.g., "18%"
                "uoM": item.uom,
                "quantity": float(item.quantity),
                "totalValues": float(item.total_values),
                "valueSalesExcludingST": float(item.value_sales_excluding_st),
                "fixedNotifiedValueOrRetailPrice": float(item.fixed_notified_value),
                "salesTaxApplicable": float(item.sales_tax_applicable),
                "salesTaxWithheldAtSource": float(item.sales_tax_withheld),
                "extraTax": float(item.extra_tax) if item.extra_tax and item.extra_tax.strip() else 0.0,
                "furtherTax": float(item.further_tax),
                "sroScheduleNo": item.sro_schedule_no or "",
                "fedPayable": float(item.fed_payable),
                "discount": float(item.discount),
                "saleType": item.sale_type or "Goods at standard rate (default)",
                "sroItemSerialNo": item.sro_item_serial_no or "",
            }
            items.append(item_payload)

        # Build main payload per IRIS spec
        payload = {
            "invoiceType": invoice.invoice_type.value,  # "Sale Invoice" or "Debit Note"
            "invoiceDate": invoice.invoice_date.strftime("%Y-%m-%d"),
            "sellerNTNCNIC": invoice.tenant.seller_ntn.replace("-", "") if invoice.tenant and invoice.tenant.seller_ntn else "",
            "sellerBusinessName": invoice.tenant.business_name if invoice.tenant else "",
            "sellerProvince": invoice.tenant.province if invoice.tenant else "",
            "sellerAddress": invoice.tenant.address if invoice.tenant else "",
            "buyerNTNCNIC": invoice.buyer_ntn_cnic.replace("-", ""),
            "buyerBusinessName": invoice.buyer_business_name,
            "buyerProvince": invoice.buyer_province,
            "buyerAddress": invoice.buyer_address,
            "buyerRegistrationType": invoice.buyer_registration_type.value,  # "Registered" or "Unregistered"
            "invoiceRefNo": invoice.invoice_ref_no if invoice.invoice_type.value == "Debit Note" else "",
            "scenarioId": invoice.scenario_id,  # Required for sandbox
            "items": items,
        }
        
        return payload

    async def submit_invoice(self, invoice: Invoice, db: Session) -> dict[str, Any]:
        """
        Submit invoice to FBR with retry logic.

        Returns the JSON response from FBR.
        Does NOT update Invoice status - caller handles DB state.
        However, it DOES Create SubmissionAttempt logs locally.
        """
        payload = self._build_payload(invoice)
        url = settings.fbr_url
        
        # Log attempt start
        logger.info("submitting_to_fbr", ref_no=invoice.invoice_ref_no, url=url)
        
        # --- DEBUGGING LOGS ---
        print(f"\n[DEBUG] FBR Submission to {url}")
        print(f"[DEBUG] Authorization Header: {self.client.headers.get('Authorization', 'MISSING')[:15]}... (Len: {len(self.client.headers.get('Authorization', ''))})")
        print(f"[DEBUG] Payload: {payload}")
        # ----------------------

        attempt_count = 0
        max_retries = settings.fbr_max_retries
        last_exception = None
        
        while attempt_count < max_retries:
            attempt_count += 1
            attempt_id = uuid.uuid4()
            
            # Create attempt log (Synchronous DB write for safety? Or Async?)
            # We are in async context.
            attempt = SubmissionAttempt(
                id=attempt_id,
                invoice_id=invoice.id,
                attempt_number=attempt_count,
                endpoint=url,
                outcome=SubmissionOutcome.UNKNOWN,
                diagnostic_id=attempt_id.hex[:8], # Use prefix of ID as diagnostic ref
            )
            db.add(attempt)
            await db.commit() # Commit start of attempt
            
            try:
                response = await self.client.post(url, json=payload)
                
                # Update attempt
                attempt.http_status = response.status_code
                attempt.response_summary = response.text[:1000] # Truncate if huge
                attempt.response_time_ms = int(response.elapsed.total_seconds() * 1000)
                
                if response.status_code == 200:
                    attempt.outcome = SubmissionOutcome.SUCCESS
                    # Parse JSON check if it really is success (FBR might return 200 with error msg)
                    try:
                        resp_json = response.json()
                        if resp_json.get("Code") != 100: # Assuming 100 is logic success? Need to verify FBR codes.
                             # For now, treat HTTP 200 as technical success.
                             pass
                    except:
                        pass
                else:
                    attempt.outcome = SubmissionOutcome.VALIDATION_ERROR # or AUTH_ERROR
                
                await db.commit()
                
                if response.status_code == 200:
                    return response.json()
                
                # If 500 or 429, maybe retry? 
                # For now, we only retry on Network Timeout (below).
                # 4xx/5xx are typically terminal for payload issues.
                return {"error": f"HTTP {response.status_code}", "body": response.text}

            except httpx.TimeoutException as e:
                last_exception = e
                attempt.outcome = SubmissionOutcome.TIMEOUT
                attempt.response_summary = str(e)
                await db.commit()
                
                if attempt_count < max_retries:
                    await asyncio.sleep(settings.fbr_retry_delay_seconds)
                    continue
            except Exception as e:
                # Other connection errors
                last_exception = e
                attempt.outcome = SubmissionOutcome.UNKNOWN # Network error
                attempt.response_summary = str(e)
                await db.commit()
                break # Don't retry generic errors blindly
        
        # If we exit loop, we failed
        return {"error": "Submission Failed", "detail": str(last_exception)}

    async def validate_invoice(self, invoice: Invoice, db: Session) -> dict[str, Any]:
        """
        Call the FBR validation endpoint (Invoice Details).
        """
        payload = self._build_payload(invoice)
        
        # Use specific validation token/url if available, else fallback
        token = settings.fbr_sandbox_invoice_detail_token or settings.fbr_auth_token
        url = settings.fbr_sandbox_invoice_detail_url
        
        if not url:
            return {"error": "Validation URL not configured"}
            
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
             async with httpx.AsyncClient(timeout=float(settings.fbr_timeout_seconds)) as client:
                response = await client.post(url, json=payload, headers=headers)
                try:
                    return response.json()
                except:
                    return {"status_code": response.status_code, "text": response.text}
        except Exception as e:
            return {"error": str(e)}

# Global instance
_fbr_service = None

def get_fbr_service() -> FBRService:
    global _fbr_service
    if _fbr_service is None:
        _fbr_service = FBRService()
    return _fbr_service
