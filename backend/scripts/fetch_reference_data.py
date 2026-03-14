"""
Fetch all FBR reference API data needed to craft sandbox payloads.

Queries: transaction types, rates (per sale type), SRO schedules, SRO items,
UOMs, HS codes with UOM, provinces, and STATL/registration type checks.
"""

import json
import urllib.request
import urllib.error
import datetime

BEARER_TOKEN = "0a1ad30e-3ef3-318c-ac42-153513973521"
BASE_REF = "https://gw.fbr.gov.pk/pdi"
BASE_DIST = "https://gw.fbr.gov.pk/dist/v1"
TODAY = datetime.date.today().strftime("%d-%b-%Y")
TODAY_ISO = datetime.date.today().isoformat()

SELLER_PROVINCE_ID = 8  # Sindh


def fetch(url, method="GET", body=None):
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status, json.loads(resp.read().decode(errors="replace"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"raw": raw[:2000]}
    except Exception as exc:
        return 0, {"error": str(exc)}


def section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def main():
    # 1. Transaction Types
    section("TRANSACTION TYPES (transtypecode)")
    code, data = fetch(f"{BASE_REF}/v1/transtypecode")
    print(f"HTTP {code} | {len(data) if isinstance(data, list) else 'error'} items")
    if isinstance(data, list):
        for t in sorted(data, key=lambda x: x.get("transactioN_TYPE_ID", 0)):
            print(f"  ID={t['transactioN_TYPE_ID']:>4}  {t['transactioN_DESC']}")

    # 2. Rates per sale type - query for key transaction type IDs
    # We need to discover which transTypeId maps to which saleType
    section("SALE TYPE TO RATE (for Sindh, today)")
    # Try a range of common transaction type IDs
    trans_ids_to_try = [18, 82, 87, 111]  # from docs
    if isinstance(data, list):
        trans_ids_to_try = [t["transactioN_TYPE_ID"] for t in data]

    for tid in trans_ids_to_try:
        url = f"{BASE_REF}/v2/SaleTypeToRate?date={TODAY}&transTypeId={tid}&originationSupplier={SELLER_PROVINCE_ID}"
        code, rates = fetch(url)
        if isinstance(rates, list) and len(rates) > 0:
            print(f"\n  transTypeId={tid}:")
            for r in rates[:10]:
                print(f"    rate_id={r.get('ratE_ID'):>4}  value={r.get('ratE_VALUE')}  desc=\"{r.get('ratE_DESC')}\"")
            if len(rates) > 10:
                print(f"    ... and {len(rates)-10} more")

    # 3. SRO Schedules - try with a few rate_ids
    section("SRO SCHEDULES")
    rate_ids_to_try = [413, 280, 734]  # from docs
    for rid in rate_ids_to_try:
        url = f"{BASE_REF}/v1/SroSchedule?rate_id={rid}&date={TODAY}&origination_supplier_csv={SELLER_PROVINCE_ID}"
        code, sros = fetch(url)
        if isinstance(sros, list) and len(sros) > 0:
            print(f"\n  rate_id={rid}:")
            for s in sros[:15]:
                print(f"    sro_id={s.get('srO_ID'):>4}  desc=\"{s.get('srO_DESC')}\"")

    # 4. SRO Items for key SRO IDs
    section("SRO ITEMS (for key SRO schedules)")
    sro_ids_to_try = [7, 8, 389]  # from docs + common
    for sid in sro_ids_to_try:
        url = f"{BASE_REF}/v2/SROItem?date={TODAY_ISO}&sro_id={sid}"
        code, items = fetch(url)
        if isinstance(items, list) and len(items) > 0:
            print(f"\n  sro_id={sid}:")
            for item in items[:10]:
                print(f"    item_id={item.get('srO_ITEM_ID'):>6}  desc=\"{item.get('srO_ITEM_DESC')}\"")
            if len(items) > 10:
                print(f"    ... and {len(items)-10} more")

    # 5. UOMs
    section("UNITS OF MEASURE (uom)")
    code, uoms = fetch(f"{BASE_REF}/v1/uom")
    if isinstance(uoms, list):
        print(f"  {len(uoms)} UOMs total:")
        for u in uoms:
            print(f"    id={u.get('uoM_ID'):>3}  desc=\"{u.get('description')}\"")

    # 6. Check registration type for known test NTNs
    section("REGISTRATION TYPE CHECKS (Get_Reg_Type)")
    test_ntns = ["0788762", "1234567", "3804564", "0786909", "7000007", "0000001"]
    for ntn in test_ntns:
        url = f"{BASE_DIST}/Get_Reg_Type"
        code, result = fetch(url, method="GET", body={"Registration_No": ntn})
        reg_type = result.get("REGISTRATION_TYPE", "?")
        status = result.get("statuscode", "?")
        print(f"  NTN={ntn}  status={status}  type={reg_type}")

    # 7. STATL checks for same NTNs
    section("STATL STATUS CHECKS")
    for ntn in test_ntns:
        url = f"{BASE_DIST}/statl"
        code, result = fetch(url, method="GET", body={"regno": ntn, "date": TODAY_ISO})
        status_code = result.get("status code", result.get("statuscode", "?"))
        status = result.get("status", "?")
        print(f"  NTN={ntn}  code={status_code}  status={status}")

    # 8. Provinces (for reference)
    section("PROVINCES")
    code, provs = fetch(f"{BASE_REF}/v1/provinces")
    if isinstance(provs, list):
        for p in provs:
            print(f"  code={p.get('stateProvinceCode'):>2}  desc={p.get('stateProvinceDesc')}")

    # 9. Document types
    section("DOCUMENT TYPES")
    code, docs = fetch(f"{BASE_REF}/v1/doctypecode")
    if isinstance(docs, list):
        for d in docs:
            print(f"  id={d.get('docTypeId'):>2}  desc={d.get('docDescription')}")


if __name__ == "__main__":
    main()
