
# PRD — IRIS 2.0 / FBR Digital Invoicing Portal

**Document version:** 0.1 (Draft)

## 1) Executive Summary
Build a portal that lets Pakistan businesses submit **Sales Invoices, Debit Notes, and Credit Notes** to **FBR Digital Invoicing / IRIS 2.0** via a JSON API.

Key characteristics:
- **Low volume, high correctness:** expected usage is infrequent (monthly).
- **Simple UX, strict duplicate prevention:** a single identifier `invoiceRefNo` is the business key. Once an `invoiceRefNo` has been submitted (or the outcome is unknown), the system blocks re-use.
- **Always-online submission** (no offline-first requirement).
- **Three product stages:** MVP → SaaS → Custom Deployment.

**Important constraint:** IRIS/FBR documentation is incomplete/absent; several integration behaviors must be validated via sandbox “trial and error”. This PRD explicitly lists those unknowns and a validation plan.

## 2) Goals / Non-Goals

### Goals
- Provide a portal UI to create and submit:
	- Sale Invoices
	- Debit Notes (must reference an existing Sales Invoice by `invoiceRefNo`)
	- Credit Notes (must reference an existing Sales Invoice by `invoiceRefNo`)
- Submit invoices to IRIS/FBR using the sandbox endpoint (known) and production endpoints (TBD later).
- Enforce strict uniqueness and reuse rules on `invoiceRefNo`:
	- Unique **per seller NTN**
	- Unique **across all types** (sale/debit/credit)
	- Warn + block if attempting to submit an already-used ref
	- Conservative behavior on uncertain outcomes (timeouts)
- Provide attempt-level audit reporting (metadata-only) including all tries.
- Provide operational visibility suitable for “no IT staff” customers.

### Non-Goals
- Finalizing production base URLs now (deferred until development/onboarding).
- Building a full accounting/ERP product.
- Implementing RBAC/MFA in early stages.
- Guaranteeing parity with FBR portal behavior without validating the IRIS/FBR API responses.

## 3) Stages & Scope

This PRD defines requirements in three stages. Later stages include everything from earlier stages unless explicitly superseded.

### Stage 1 — MVP
**Purpose:** deliver a working end-to-end submission portal with minimal operational and commercial complexity.

In scope:
- Single deployed portal (vendor-managed) with basic login.
- Create invoice documents and POST to sandbox/prod (prod URLs TBD).
- Strict duplicate prevention and conservative blocking.
- Audit attempt ledger (metadata-only) + monthly export (PDF summary + CSV detail).
- Basic monitoring/alerting for submission failures.

Out of scope:
- Billing/subscriptions.
- Self-serve tenant provisioning.
- On-prem packaging.

### Stage 2 — SaaS (Multi-tenant)
**Purpose:** scale MVP into a multi-tenant product where each seller configures their own identity and submits under their own seller NTN.

In scope:
- Multi-tenant isolation (data + configuration separated per seller NTN/tenant).
- Tenant-level configuration of IRIS/FBR credentials (auth flow still to be validated).
- Tenant-scoped uniqueness enforcement (per seller NTN).
- Enhanced observability and support tooling (diagnostic IDs, support exports).

Out of scope:
- Complex org hierarchy, RBAC, or MFA (explicitly “not yet”).

### Stage 3 — Custom Deployment (Single-tenant / On-prem-like)
**Purpose:** deliver a “custom deployment” option for higher security and single-seller environments.

In scope:
- Single tenant only (one seller/company).
- Vendor-managed deployment model (as decided); installation specifics TBD.
- Configurable logging/retention policies (while keeping “metadata-only audit report” behavior consistent unless customer requests otherwise).

Out of scope:
- Fully customer-managed operations unless explicitly contracted.

## 4) Stakeholders & Responsibilities (RACI)

| Area | Responsible (R) | Accountable (A) | Consulted (C) | Informed (I) |
|---|---|---|---|---|
| Product requirements & UX | Product Owner | Product Owner | Tax/Compliance advisor | Dev team |
| IRIS/FBR integration validation | Dev team | Tech Lead | Product Owner | Support |
| Security posture (SaaS) | Tech Lead | Tech Lead | Product Owner | Users |
| Support operations | Support/Dev team | Product Owner | Tech Lead | Users |
| Release management | Dev team | Tech Lead | Product Owner | Users |

## 5) Current State vs Target State

### Current State
- Businesses historically used an FBR portal and got only “submitted successfully” / “failed to submit” feedback.
- For IRIS/FBR API, documentation is sparse; token acquisition, response schema, and status endpoints are unknown.
- Workspace contains:
	- Example JSON payload structure
	- A C# submission example using Bearer token
	- An environment note with incomplete URLs

### Target State
- A portal where users can:
	1) enter invoice data,
	2) validate client-side,
	3) submit to IRIS/FBR,
	4) see a clear outcome state,
	5) export monthly audit reports including all tries.

**Boundaries:**
- Portal is the system of record for invoice submissions and attempts.
- IRIS/FBR is the external authority for acceptance/recording.

## 6) Detailed Workflows

### 6.1 Happy Path — Sales Invoice
1. User logs into the portal (Stage 1/2/3).
2. User creates a Sales Invoice document.
3. User enters `invoiceRefNo` (single identifier field).
	 - Portal may suggest next `invoiceRefNo` based on last successful ref (see 9.3).
4. Client-side validation runs:
	 - Required fields present
	 - Valid formats
	 - Numeric fields are non-negative
	 - At least 1 item
5. Duplicate checks:
	 - If `invoiceRefNo` has already been successfully recorded/submitted (per portal records), **warn + block**.
	 - If `invoiceRefNo` has a prior “Unknown outcome” attempt, **block** (conservative).
6. User clicks Submit.
7. UI disables Submit while in-flight.
8. System POSTs payload to IRIS/FBR.
9. On success (provisionally HTTP 2xx, pending validation):
	 - Mark attempt as “Submitted (Success)”
	 - Clear the form and show confirmation
10. Audit ledger records the attempt (metadata-only).

### 6.2 Happy Path — Debit/Credit Note
1. User creates a Debit Note or Credit Note.
2. User must provide a reference to an existing Sales Invoice using the Sales Invoice’s `invoiceRefNo`.
3. Portal enforces that referenced Sales Invoice exists **and** is in “Recorded/Submitted Success” state.
4. Submit flow follows the same mechanics as Sales Invoice.

### 6.3 Timeout / Unknown Outcome Flow (Conservative)
Definition: a “timeout” is when the system does not receive a response within the configured timeout (Stage default: 30s).

1. System sends POST and times out.
2. System performs **2 additional automatic retries** (total attempts = 3), with **2s delay** between retries.
3. If all 3 attempts time out:
	 - Display toast: “Request timed out. Please wait and try again.”
	 - Keep form contents (user may retry later).
	 - Record attempt outcome as **Unknown**.
4. Conservative block:
	 - `invoiceRefNo` is blocked from reuse once Unknown exists (until reconciliation/validation clarifies recorded/not recorded).

### 6.4 User Manual Retry (Unlimited)
- User can manually retry from the UI at any time.
- Manual retries do not introduce artificial delays.
- Duplicate policy still applies:
	- If portal believes ref is already recorded, block.
	- If ref is Unknown, block (conservative) unless explicitly cleared by reconciliation.

### 6.5 Validation Error Flow
- If IRIS/FBR returns structured field errors:
	- Map to UI fields and display field-level errors.
- If IRIS/FBR returns unstructured errors:
	- Show a generic error with a safe “raw server message” panel (sanitized/truncated) and include a diagnostic ID.

## 7) External Integration: IRIS 2.0 / FBR Digital Invoicing

### 7.1 Endpoint Inventory
**Known (Sandbox):**
- Invoice submission (sandbox): `https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata_sb`

**Unknown / To be confirmed (Sandbox & Production):**
- Token acquisition / login endpoint(s)
- Any status/query endpoint(s)
- Any debit/credit note specific endpoint(s) if separate
- Production base URLs

### 7.2 Auth / Token Strategy (Draft)
Current evidence in workspace indicates:
- Requests use `Authorization: Bearer <token>`.

Unknowns (must validate):
- How tokens are obtained (portal NTN+password vs separate API credentials)
- Token expiry/refresh rules

Design requirement:
- Treat token handling as configurable per environment and per tenant (in SaaS).

### 7.3 Request Contract (Current Draft)
Baseline request shape is based on the sample payload in JSON Format.txt.

Top-level fields (draft):
- `invoiceType` (string)
- `invoiceDate` (string, expected `yyyy-MM-dd`)
- Seller fields: `sellerNTNCNIC`, `sellerBusinessName`, `sellerProvince`, `sellerAddress`
- Buyer fields: `buyerNTNCNIC`, `buyerBusinessName`, `buyerProvince`, `buyerAddress`, `buyerRegistrationType`
- `invoiceRefNo` (string) — the system’s key identifier
- `scenarioId` (string)
- `items[]` (array)

Items fields (draft):
- `hsCode`, `productDescription`, `rate`, `uoM`, `quantity`, `totalValues`, `valueSalesExcludingST`,
	`fixedNotifiedValueOrRetailPrice`, `salesTaxApplicable`, `salesTaxWithheldAtSource`, `extraTax`, `furtherTax`,
	`sroScheduleNo`, `fedPayable`, `discount`, `saleType`, `sroItemSerialNo`

**To validate:** required/optional fields, enums, max lengths, and numeric constraints.

### 7.4 Response Contract (Unknown)
No official response schema is currently available in the workspace.

**Trial-and-error plan:** capture and document:
- success payload fields (receipt/reference IDs if any)
- validation error payload structure
- duplicate response behavior

## 8) Status Codes & Error Taxonomy (Portal-side)

Because IRIS/FBR error schemas are unknown, the portal uses a taxonomy that can be mapped from HTTP and observed payloads.

### 8.1 Categories
- **Validation (Non-retryable):** 400/422-like responses with field errors
- **Auth (Non-retryable until user fixes creds):** 401/403
- **Duplicate (Non-retryable):** server indicates ref already used
- **Transient (Retryable only by system within limits):** timeouts only (per product decision)
- **Unknown:** anything not classifiable

### 8.2 UI behaviors
- Non-retryable: show error + diagnostic ID; do not auto-retry.
- Timeout: auto-retry twice; if still timeout, show toast and mark Unknown.

## 9) Idempotency + invoiceRefNo Policy

### 9.1 Core rules
- `invoiceRefNo` is the portal’s sole invoice identifier for FBR submission.
- Uniqueness scope: **unique per seller NTN** and **unique across all doc types**.
- Once an `invoiceRefNo` has a successful submission, it can never be reused.
- If outcome is Unknown (timeouts), the portal blocks reusing the same ref (conservative) until cleared.

### 9.2 Duplicate handling
- Client-side: if an `invoiceRefNo` is known as used, warn + block.
- Server-side: expected to block duplicates as well (must validate).
- No override path.

### 9.3 Suggest-next (+1) strategy
The portal may suggest the next `invoiceRefNo` based on the last successfully submitted invoiceRefNo.

Proposed algorithm:
- If prior ref has trailing digits: increment trailing integer by 1; preserve leading zeros width.
- If no trailing digits: provide no suggestion.

Examples:
- `1005` → `1006`
- `INV-0009` → `INV-0010`
- `INV-A` → (no suggestion)

Important: suggestion is convenience; final uniqueness is enforced at save/submit.

## 10) Retries / Backoff / Timeouts / Rate limits

### 10.1 Timeouts
- Default HTTP timeout: **30 seconds**.

### 10.2 Automatic retries
- Trigger: **timeout only**.
- Attempts: 1 initial + 2 retries (total 3).
- Delay: **2 seconds** between retries.
- No automatic retries for non-timeout errors.

### 10.3 Manual retries
- Unlimited from UI.
- Portal must avoid infinite “hammering”:
	- If ref is Known-Success or Unknown, block resubmission (conservative).

### 10.4 Rate limits
- Unknown; must validate via sandbox or IRIS guidance.

## 11) Data Model & Mapping

### 11.1 Canonical model (portal)
Each document stores:
- Tenant/seller identity (seller NTN)
- Document type (sale/debit/credit)
- `invoiceRefNo` (string, unique)
- Header fields (date, parties)
- Line items
- Attempt ledger (append-only)

### 11.2 Field mapping table (Portal → IRIS/FBR)
Because source is the portal UI, the mapping is direct.

| Portal Field | Target JSON Field | Transform | Validation | Error behavior |
|---|---|---|---|---|
| Invoice reference number | `invoiceRefNo` | none | required, unique per seller NTN | warn+block |
| Invoice type | `invoiceType` | map from doc type | required | block |
| Invoice date | `invoiceDate` | format `yyyy-MM-dd` | required | block |
| Seller NTN | `sellerNTNCNIC` | none | required | block |
| Buyer NTN/CNIC | `buyerNTNCNIC` | none | required | block |
| Items | `items[]` | none | >= 1 item | block |
| Amount/tax fields | per item fields | none | non-negative numeric | block |

**To validate:** rounding/precision rules, allowed values for `rate`, `buyerRegistrationType`, `scenarioId`, `saleType`, etc.

### 11.3 Rounding & precision
Currently unknown; must be validated.
Interim approach:
- Preserve user-entered numeric values.
- Validate non-negative and basic consistency checks.
- Add a validation mode to warn users when totals appear inconsistent.

## 12) Edge Cases & Business Rules

Confirmed:
- Debit/Credit notes must reference an existing Sales Invoice by `invoiceRefNo`.
- If referenced Sales Invoice does not exist locally (or is not recorded), block submission.

To validate:
- Whether IRIS/FBR enforces this linkage and how.
- Whether `invoiceRefNo` uniqueness is per seller NTN and across all doc types.

## 13) Security / Privacy / Compliance

### 13.1 Authentication
- Portal login initially mirrors “NTN + password” UX.
- No MFA initially.

### 13.2 Data handling
- Audit logs and audit exports are **metadata-only**.
- Store diagnostic IDs and payload hashes as needed; do not store bearer tokens in logs.

### 13.3 Retention
- Default retention: **12 months** for attempt metadata and audit exports.
- Configurable per tenant/deployment in later stages.

## 14) Observability & Operations

### 14.1 Logging (metadata only)
Per attempt, capture:
- timestamp
- seller NTN
- `invoiceRefNo`
- document type
- attempt number
- endpoint
- timeout/HTTP status
- diagnostic ID
- response summary (sanitized)

### 14.2 Metrics (minimum)
- submissions attempted / succeeded / failed / unknown
- timeouts and retry counts
- duplicate blocks

### 14.3 Alerts
- sustained timeouts
- auth failures spikes
- repeated duplicate blocks (possible user confusion)

### 14.4 Support model
- Assume no customer IT staff.
- Developer/support response target: fix within a week (given low submission frequency).

## 15) Testing & Acceptance Criteria

### 15.1 Contract tests
- Validate request JSON formation matches sample structure.
- Validate required fields and data types.

### 15.2 Negative tests
- Missing buyer NTN/CNIC blocks
- Duplicate `invoiceRefNo` blocks
- Debit/credit note referencing missing sale invoice blocks

### 15.3 Sandbox validation tests (trial-and-error)
- Capture success response payload and confirm “recorded” signal.
- Duplicate submission behavior for same `invoiceRefNo`.
- Error payload schema for validation failures.

### 15.4 Acceptance gates
- Successfully submit at least one of each doc type in sandbox.
- Confirm behavior of duplicate submissions.
- Confirm portal prevents duplicate reuse forever.

## 16) Rollout Plan & Rollback Strategy

### Rollout
- Stage 1 MVP: limited pilot tenants.
- Stage 2 SaaS: broaden access; add tenant management.
- Stage 3 Custom deployment: deliver to contracted customers.

### Rollback
- Feature-flag submission capability per tenant.
- If IRIS/FBR behavior changes, disable submission temporarily while preserving drafted invoices.

## 17) Mandatory “Poke Holes” Critique (Failure Modes + Mitigations)

The following failure modes must be explicitly designed for:

1. **Bearer token acquisition unknown / fails** → block submission; provide actionable UI + diagnostic ID.
2. **Token expires mid-submit** → treat as auth failure; require user re-login/config refresh.
3. **Network timeout after server recorded invoice** → conservative Unknown state; block reuse; reconcile later.
4. **User retries repeatedly after timeout** → portal blocks by ref; guide user to wait/support.
5. **Duplicate `invoiceRefNo` due to suggestion collisions** → enforce uniqueness on save/submit; show conflict resolution.
6. **Server returns 2xx but not actually “recorded”** → must validate; if discovered, adjust success semantics.
7. **Validation errors returned without field paths** → show generic error + raw message fallback.
8. **Schema changes** → fail safely; alert; require update.
9. **Debit/credit note references non-existent sale invoice** → block locally; show guidance.
10. **Rate limiting (429) despite low volume** → no auto-retry (per decision); message user; add later if needed.

High-risk assumptions to confirm early:
- Existence of a “recorded” signal.
- Exact duplicate behavior by `invoiceRefNo`.
- Auth/token acquisition flow.

## 18) Appendix

### 18.1 Final Gap Log (as of this draft)
- Auth/token acquisition endpoints and lifecycle (TBD; trial-and-error)
- Success/recorded semantics (TBD; trial-and-error)
- Error response schema (TBD; trial-and-error)
- Rounding/precision rules (TBD)

### 18.2 Assumptions Register (as of this draft)
- HTTP 2xx indicates submitted/recorded (unconfirmed)
- Duplicate behavior is enforced by `invoiceRefNo` (unconfirmed)
- No status endpoint exists (unconfirmed)

### 18.3 Decision Log (as of this draft)
- Single identifier `invoiceRefNo` for all doc types
- Strict warn+block duplicates; no override
- Conservative Unknown handling; block reuse
- Timeout 30s; 2 timeout-only retries with 2s delay
- Metadata-only audit; include all tries

### 18.4 Glossary
- **NTN**: National Tax Number (seller identifier)
- **CNIC**: National identity number (buyer identifier in some cases)
- **IRIS/FBR**: Pakistan Federal Board of Revenue digital invoicing platform
- **`invoiceRefNo`**: Portal invoice reference number; used as submission key to IRIS/FBR

