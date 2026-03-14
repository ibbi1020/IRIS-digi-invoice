"""
Send all 12 required sandbox scenarios to the IRIS FBR sandbox API.

Each payload has been validated through trial-and-error against the live
sandbox. Key findings documented inline.

Run with:
    python scripts/send_sandbox_scenarios.py
"""

import json
import re
import urllib.request
import urllib.error
import datetime

SANDBOX_URL = "https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata_sb"
BEARER_TOKEN = "0a1ad30e-3ef3-318c-ac42-153513973521"

SELLER = {
    "sellerNTNCNIC": "3804564",
    "sellerBusinessName": "PAPEREXCHANGE",
    "sellerProvince": "Sindh",
    "sellerAddress": "Karachi",
}

BUYER_UNREGISTERED = {
    "buyerNTNCNIC": "",
    "buyerBusinessName": "Walk-in Customer",
    "buyerProvince": "Sindh",
    "buyerAddress": "Karachi",
    "buyerRegistrationType": "Unregistered",
}

BUYER_REGISTERED = {
    "buyerNTNCNIC": "0786909",
    "buyerBusinessName": "FERTILIZER MANUFAC IRS NEW",
    "buyerProvince": "Sindh",
    "buyerAddress": "Karachi",
    "buyerRegistrationType": "Registered",
}

TODAY = datetime.date.today().isoformat()


def _parse_json_response(raw: bytes) -> dict:
    text = raw.decode(errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = re.sub(r",(\s*[}\]])", r"\1", text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"raw": text[:1000]}


def _standard_item(
    sale_type,
    *,
    hs_code="0101.2100",
    description="Test Item for DI Sandbox",
    rate="18%",
    uom="Numbers, pieces, units",
    quantity=1.0,
    value_excl=1000.00,
    st=180.00,
    total=1180.00,
    fixed_value=0.00,
    withheld=0.00,
    extra_tax=0.00,
    further_tax=0.00,
    fed=0.00,
    sro_schedule_no="",
    sro_item_serial_no="",
):
    """Build a standard item payload. All tax fields included as numeric 0.00."""
    return {
        "hsCode": hs_code,
        "productDescription": description,
        "rate": rate,
        "uoM": uom,
        "quantity": quantity,
        "totalValues": total,
        "valueSalesExcludingST": value_excl,
        "fixedNotifiedValueOrRetailPrice": fixed_value,
        "salesTaxApplicable": st,
        "salesTaxWithheldAtSource": withheld,
        "extraTax": extra_tax,
        "furtherTax": further_tax,
        "sroScheduleNo": sro_schedule_no,
        "fedPayable": fed,
        "discount": 0.00,
        "saleType": sale_type,
        "sroItemSerialNo": sro_item_serial_no,
    }


def _reduced_rate_item(
    *,
    rate="1%",
    st=10.00,
    total=1010.00,
    sro_schedule_no="EIGHTH SCHEDULE Table 1",
    sro_item_serial_no="70",
):
    """Build a reduced-rate item. extraTax must be empty string "" — FBR rejects
    both numeric 0.00 (error 0091) and omitted/null (error 0300)."""
    return {
        "hsCode": "0101.2100",
        "productDescription": "Test Item for DI Sandbox",
        "rate": rate,
        "uoM": "Numbers, pieces, units",
        "quantity": 1.0,
        "totalValues": total,
        "valueSalesExcludingST": 1000.00,
        "fixedNotifiedValueOrRetailPrice": 0.00,
        "salesTaxApplicable": st,
        "salesTaxWithheldAtSource": 0.00,
        "extraTax": "",
        "furtherTax": 0.00,
        "sroScheduleNo": sro_schedule_no,
        "fedPayable": 0.00,
        "discount": 0.00,
        "saleType": "Goods at Reduced Rate",
        "sroItemSerialNo": sro_item_serial_no,
    }


def _third_schedule_item():
    """Build a 3rd-schedule item. Requires a valid 3rd-schedule HS code
    (e.g. 3304.1000 cosmetics) and fixedNotifiedValueOrRetailPrice > 0."""
    return _standard_item(
        "3rd Schedule Goods",
        hs_code="3304.1000",
        description="Lip make-up preparations",
        rate="18%",
        fixed_value=1000.00,
    )


SCENARIOS = [
    # --- Already validated in previous iterations ---
    {
        "id": "SN001",
        "desc": "Goods at Standard Rate to Registered Buyers",
        "buyer": BUYER_REGISTERED,
        "items": [_standard_item("Goods at standard rate (default)")],
    },
    {
        "id": "SN002",
        "desc": "Goods at Standard Rate to Unregistered Buyers",
        "buyer": BUYER_UNREGISTERED,
        "items": [_standard_item("Goods at standard rate (default)")],
    },
    {
        "id": "SN005",
        "desc": "Reduced Rate Sale",
        "buyer": BUYER_UNREGISTERED,
        "items": [_reduced_rate_item()],
    },
    {
        "id": "SN008",
        "desc": "Sale of 3rd Schedule Goods",
        "buyer": BUYER_UNREGISTERED,
        "items": [_third_schedule_item()],
    },
    {
        "id": "SN010",
        "desc": "Telecom services",
        "buyer": BUYER_UNREGISTERED,
        "items": [_standard_item(
            "Telecommunication services",
            rate="19.5%", st=195.00, total=1195.00,
        )],
    },
    {
        "id": "SN016",
        "desc": "Processing / Conversion of Goods",
        "buyer": BUYER_UNREGISTERED,
        "items": [_standard_item("Processing/Conversion of Goods")],
    },
    {
        "id": "SN017",
        "desc": "Goods where FED is Charged in ST Mode",
        "buyer": BUYER_UNREGISTERED,
        "items": [_standard_item(
            "Goods (FED in ST Mode)",
            rate="17%", st=170.00, total=1170.00, fed=170.00,
        )],
    },
    {
        "id": "SN021",
        "desc": "Sale of Cement / Concrete Block",
        "buyer": BUYER_UNREGISTERED,
        "items": [_standard_item(
            "Cement /Concrete Block",
            hs_code="2523.2900", uom="KG",
            rate="Rs.2", st=2.00, total=1002.00,
        )],
    },
    {
        "id": "SN024",
        "desc": "Goods Listed in SRO 297(1)/2023",
        "buyer": BUYER_UNREGISTERED,
        "items": [_standard_item(
            "Goods as per SRO.297(|)/2023",
            rate="25%", st=250.00, total=1250.00,
            sro_schedule_no="297(I)/2023-Table-I",
            sro_item_serial_no="3",
        )],
    },
    {
        "id": "SN026",
        "desc": "Sale to End Consumer by Retailers (standard rate)",
        "buyer": BUYER_UNREGISTERED,
        "items": [_standard_item("Goods at standard rate (default)")],
    },
    {
        "id": "SN027",
        "desc": "Sale to End Consumer by Retailers (3rd schedule)",
        "buyer": BUYER_UNREGISTERED,
        "items": [_third_schedule_item()],
    },
    {
        "id": "SN028",
        "desc": "Sale to End Consumer by Retailers (reduced rate)",
        "buyer": BUYER_UNREGISTERED,
        "items": [_reduced_rate_item()],
    },
]


def send(payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        SANDBOX_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status, _parse_json_response(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, _parse_json_response(e.read())
    except Exception as exc:
        return 0, {"error": str(exc)}


def main():
    total = len(SCENARIOS)
    passed = 0
    failed = 0

    print(f"Sending {total} sandbox scenarios to FBR IRIS...\n")

    for scenario in SCENARIOS:
        sid = scenario["id"]
        desc = scenario["desc"]

        payload = {
            "invoiceType": "Sale Invoice",
            "invoiceDate": TODAY,
            **SELLER,
            **scenario["buyer"],
            "invoiceRefNo": "",
            "scenarioId": sid,
            "items": scenario["items"],
        }

        http_code, body = send(payload)
        vr = body.get("validationResponse", {})
        status_code = vr.get("statusCode", "?")
        status = vr.get("status", "?")
        invoice_num = body.get("invoiceNumber", "N/A")
        error = vr.get("error", "")

        if http_code == 200 and status_code == "00" and status.lower() == "valid":
            passed += 1
            print(f"  [OK]   {sid} | {desc}")
            print(f"         FBR# {invoice_num}")
        else:
            failed += 1
            item_statuses = vr.get("invoiceStatuses") or []
            item_errors = "; ".join(
                f"item{s.get('itemSNo')}: [{s.get('errorCode')}] {s.get('error')}"
                for s in item_statuses if s.get("statusCode") == "01"
            ) if item_statuses else ""
            header_err = f"[{vr.get('errorCode', '')}] {error}" if error else ""
            print(f"  [FAIL] {sid} | {desc}")
            print(f"         http={http_code} statusCode={status_code}")
            if header_err:
                print(f"         {header_err}")
            if item_errors:
                print(f"         {item_errors}")

    print(f"\n{'='*60}")
    print(f"  Result: {passed}/{total} scenarios passed")
    if failed:
        print(f"  {failed} scenario(s) failed")
    else:
        print(f"  All scenarios passed!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
