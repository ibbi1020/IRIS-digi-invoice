"""
Send the 12 target sandbox scenarios directly to the IRIS FBR sandbox API.

This script uses curated, scenario-specific payloads based on the IRIS
documentation and the FBR reference endpoints. Some scenarios still depend on
seller-profile-specific or buyer-specific reference data, so the script prints a
checklist and current blockers before sending.

Run with:
    python3 scripts/send_sandbox_scenarios.py

Optional:
    IRIS_REGISTERED_BUYER_NTN=1234567 python3 scripts/send_sandbox_scenarios.py
"""

import os
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
    "buyerNTNCNIC": os.getenv("IRIS_REGISTERED_BUYER_NTN", ""),
    "buyerBusinessName": os.getenv("IRIS_REGISTERED_BUYER_NAME", "Registered Buyer"),
    "buyerProvince": "Sindh",
    "buyerAddress": "Karachi",
    "buyerRegistrationType": "Registered",
}

TODAY = datetime.date.today().isoformat()

CHECKLIST = [
    ("SN002", "Validated working baseline payload."),
    ("SN003", "Uses steel-specific HS/UOM candidate; may still need sector-approved HS mapping."),
    ("SN004", "Uses ship-breaking HS/UOM candidate; may still need sector-approved HS mapping."),
    ("SN005", "Uses reduced-rate candidate plus FBR SRO schedule and item serial; FBR still returns conflicting `extraTax` validation."),
    ("SN006", "Uses FBR rate text `Exempt` plus exempt SRO schedule and item serial."),
    ("SN007", "Uses zero-rate candidate plus FBR SRO schedule and item serial."),
    ("SN008", "Adds fixed/notified retail price for 3rd schedule testing."),
    ("SN009", "Needs a real registered buyer NTN in IRIS_REGISTERED_BUYER_NTN to fully validate."),
    ("SN010", "Validated working telecom payload."),
    ("SN011", "FBR currently reports `Provided scenario does not exists` for this seller/token."),
    ("SN021", "Uses cement-specific rupee rate candidate from FBR reference API."),
    ("SN028", "Uses reduced-rate retailer candidate plus FBR SRO schedule; FBR still returns conflicting `extraTax` validation."),
]


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


def make_item(
    sale_type,
    *,
    hs_code="0101.2100",
    rate="18%",
    uom="Numbers, pieces, units",
    quantity=1.0,
    st=180.00,
    total=1180.00,
    value_excl=1000.00,
    fixed_value=0.00,
    withheld=0.00,
    further_tax=0.00,
    extra_tax=0.00,
    fed=0.00,
    sro_schedule_no="",
    sro_item_serial_no="",
):
    item = {
        "hsCode": hs_code,
        "productDescription": "Test Item for DI Sandbox",
        "rate": rate,
        "uoM": uom,
        "quantity": quantity,
        "totalValues": total,
        "valueSalesExcludingST": value_excl,
        "fixedNotifiedValueOrRetailPrice": fixed_value,
        "salesTaxApplicable": st,
        "salesTaxWithheldAtSource": withheld,
        "sroScheduleNo": sro_schedule_no,
        "discount": 0.00,
        "saleType": sale_type,
        "sroItemSerialNo": sro_item_serial_no,
    }
    if extra_tax is not None:
        item["extraTax"] = extra_tax
    if further_tax is not None:
        item["furtherTax"] = further_tax
    if fed is not None:
        item["fedPayable"] = fed
    return item


SCENARIOS = [
    {
        "scenarioId": "SN002",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item("Goods at standard rate (default)"),
    },
    {
        "scenarioId": "SN003",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item(
            "Steel melting and re-rolling",
            hs_code="7214.2000",
            uom="KG",
            rate="18%",
        ),
    },
    {
        "scenarioId": "SN004",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item(
            "Ship breaking",
            hs_code="7204.4990",
            uom="KG",
            rate="18%",
        ),
    },
    {
        "scenarioId": "SN005",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item(
            "Goods at Reduced Rate",
            rate="1%",
            st=10.00,
            total=1010.00,
            extra_tax=None,
            sro_schedule_no="EIGHTH SCHEDULE Table 1",
            sro_item_serial_no="70",
        ),
    },
    {
        "scenarioId": "SN006",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item(
            "Exempt goods",
            rate="Exempt",
            st=0.00,
            total=1000.00,
            sro_schedule_no="NINTH SCHEDULE",
            sro_item_serial_no="5",
        ),
    },
    {
        "scenarioId": "SN007",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item(
            "Goods at zero-rate",
            rate="0%",
            st=0.00,
            total=1000.00,
            sro_schedule_no="FIFTH SCHEDULE",
            sro_item_serial_no="1(i)",
        ),
    },
    {
        "scenarioId": "SN008",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item(
            "3rd Schedule Goods",
            hs_code="2202.1000",
            rate="18%",
            fixed_value=1000.00,
        ),
    },
    {
        "scenarioId": "SN009",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_REGISTERED,
        "item": make_item(
            "Cotton ginners",
            hs_code="5201.0000",
            uom="KG",
            rate="18%",
            withheld=180.00,
        ),
    },
    {
        "scenarioId": "SN010",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item(
            "Telecommunication services",
            rate="19.5%",
            st=195.00,
            total=1195.00,
        ),
    },
    {
        "scenarioId": "SN011",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item(
            "Toll Manufacturing",
            hs_code="7214.2000",
            uom="KG",
            rate="18%",
        ),
    },
    {
        "scenarioId": "SN021",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item(
            "Cement /Concrete Block",
            hs_code="2523.2900",
            uom="KG",
            quantity=1.0,
            rate="Rs.2",
            st=2.00,
            total=1002.00,
        ),
    },
    {
        "scenarioId": "SN028",
        "invoiceType": "Sale Invoice",
        "buyer": BUYER_UNREGISTERED,
        "item": make_item(
            "Goods at Reduced Rate",
            rate="1%",
            st=10.00,
            total=1010.00,
            extra_tax=None,
            sro_schedule_no="EIGHTH SCHEDULE Table 1",
            sro_item_serial_no="70",
        ),
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
        body = _parse_json_response(resp.read())
        return resp.status, body
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, _parse_json_response(raw)
    except Exception as exc:
        return 0, {"error": str(exc)}


def main():
    results = {"success": 0, "failed": 0}

    print("Sandbox payload checklist:")
    for scenario_id, note in CHECKLIST:
        print(f"- {scenario_id}: {note}")
    print()

    for scenario in SCENARIOS:
        scenario_id = scenario["scenarioId"]
        inv_type = scenario["invoiceType"]
        buyer = scenario["buyer"]
        item = scenario["item"]

        if scenario_id == "SN009" and not buyer["buyerNTNCNIC"]:
            results["failed"] += 1
            print(f"[SKIP] {scenario_id} | missing IRIS_REGISTERED_BUYER_NTN for registered-buyer scenario")
            continue

        payload = {
            "invoiceType": inv_type,
            "invoiceDate": TODAY,
            **SELLER,
            **buyer,
            "invoiceRefNo": "",
            "scenarioId": scenario_id,
            "items": [item],
        }

        http_code, body = send(payload)
        validation = body.get("validationResponse", {})
        status_code = validation.get("statusCode", "?")
        invoice_num = body.get("invoiceNumber", "N/A")
        error = validation.get("error", "")

        if http_code == 200 and status_code == "00":
            results["success"] += 1
            print(f"[OK]   {scenario_id} | http={http_code} | FBR#={invoice_num}")
        else:
            results["failed"] += 1
            item_statuses = validation.get("invoiceStatuses") or []
            item_errors = "; ".join(
                f"item{s.get('itemSNo')}: [{s.get('errorCode')}] {s.get('error')}"
                for s in item_statuses if s.get("statusCode") == "01"
            ) if item_statuses else error
            print(f"[FAIL] {scenario_id} | http={http_code} | statusCode={status_code} | {item_errors or body}")

    print(f"\nDone: {results['success']}/12 successful, {results['failed']} failed")


if __name__ == "__main__":
    main()
