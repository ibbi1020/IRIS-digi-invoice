# IRIS Digital Invoicing - Backend Implementation Status

**Generated**: 2026-01-23
**Current Phase**: Milestone 5 (FBR Integration)

## 📌 Executive Summary
We have successfully built the core Application Layer of the metadata-driven invoicing engine. The system now supports secure multi-tenant authentication, comprehensive Invoice lifecycle management (CRUD), and enforces strict FBR compliance rules (validation, sequencing, uniqueness).

The next phase bridges the gap between our internal system and the external FBR IRIS 2.0 API.

---

## 🚦 Roadmap & Status

| Phase | Milestone | Status | Description |
|:---:|:---|:---:|:---|
| 1 | **Foundation** | ✅ Done | Project scaffold, Docker/Postgres, Config |
| 2 | **Data Models** | ✅ Done | Schema for Tenant, User, Invoice, Items |
| 3 | **Auth** | ✅ Done | JWT, Bcrypt, Tenant Isolation |
| 4 | **Invoice CRUD** | ✅ Done | Full lifecycle management + Validation |
| 5 | **FBR Integration** | 🚧 Next | API Client, Submission, Retries |
| 6 | **Reporting** | 📅 Pending | Audit logs, Monthly reports |

---

## 📝 Detailed Progress

### ✅ Milestone 1: Boilerplate & Infrastructure
*   **Infrastructure**: Dockerized PostgreSQL `iris_invoicing` database.
*   **Configuration**: Environment-based settings (Dev/Prod) using `pydantic-settings`.
*   **Quality**: Configured `ruff` (linting), `black` (formatting), and `pytest` (testing).

### ✅ Milestone 2: Database Schema
*   **ORM**: SQLAlchemy 2.0 Async models.
*   **Entities**:
    *   `Tenant`: Represents the seller (Company).
    *   `User`: Authentication entities linked to Tenants.
    *   `Invoice`: The core document (header).
    *   `InvoiceItem`: Line items with FBR-specific tax fields.
    *   `SubmissionAttempt`: Audit log for FBR interactions.
*   **Migrations**: Alembic pipeline established.

### ✅ Milestone 3: Authentication & Security
*   **Security**: Implement `bcrypt` password hashing (customized for Python 3.14 compat).
*   **Tokens**: JWT Access Tokens with 24h expiry.
*   **Access Control**: `get_current_user` dependency ensures all API actions are securely scoped to the caller's Tenant.

### ✅ Milestone 4: Invoice Engine (CRUD)
*   **API**:
    *   `POST /invoices`: Create Draft with nested validation.
    *   `GET /invoices`: List with pagination & filters.
    *   `PUT /invoices/{id}`: Edit Drafts.
    *   `DELETE /invoices/{id}`: Remove Drafts.
    *   `GET /invoices/suggest-ref`: Smart auto-increment logic.
*   **Business Logic**:
    *   **Uniqueness**: Blocks duplicate `invoiceRefNo` for the same Tenant.
    *   **Immutability**: Prevents editing/deleting submitted invoices.
    *   **Relationships**: Enforces Debit/Credit notes must link to valid Sales Invoices.
*   **Verification**:
    *   Integration tests cover the full Auth -> CRUD lifecycle.

---

## 🚀 Next Steps: Milestone 5 (FBR Submission)

We are now ready to implement the connector to the FBR API.

### Key Tasks:
1.  **FBR Service**: Create `app/services/fbr_service.py` to handle HTTP SOAP/REST calls.
2.  **Submission Endpoint**: `POST /invoices/{id}/submit`.
3.  **Resilience**: Implement reliable retry logic (only retry on timeout/network error, not on validation error).
4.  **State Management**: Handle transitions (`DRAFT` → `SUBMITTED` or `FAILED`).

### Technical Challenges to Address:
*   FBR API Latency handling.
*   Mapping our `Invoice` model to the exact FBR JSON/XML payload structure.
*   Handling Sandbox vs Production credentials.

### Sandbox Payload Checklist
- [x] Bearer token is valid for seller NTN `3804564` and seller name `PAPEREXCHANGE`.
- [x] Direct sandbox posting works end-to-end for `SN002`, `SN010`, and `SN021` with HTTP `200` and valid FBR invoice numbers.
- [ ] `SN003` and `SN004` need commodity-appropriate HS codes and UOM values for steel and ship-breaking sale types.
- [ ] `SN005`, `SN006`, `SN007`, and `SN028` need both a valid `sroScheduleNo` and a matching `sroItemSerialNo` from the reference APIs.
- [ ] `SN008` must include `fixedNotifiedValueOrRetailPrice` and a 3rd-schedule-compatible commodity payload.
- [ ] `SN009` needs a real registered buyer NTN/CNIC plus cotton-ginner-specific tax treatment.
- [ ] `SN011` is currently rejected by FBR as `Provided scenario does not exists` for this token/account profile.
- [x] `SN021` succeeds when using the cement-specific rate format (`Rs.2`, `Rs.3`, `Rs.5`, or `Rs.10`) instead of a percentage rate.
