# IRIS 2.0 – FBR Digital Invoicing Portal Frontend

A production-ready Next.js frontend for submitting invoices, debit notes, and credit notes to Pakistan's FBR (Federal Board of Revenue) via a Backend-for-Frontend (BFF) API.

## Quick Start

```bash
# Install dependencies
npm install

# Run development server (with MSW mocking enabled)
npm run dev

# Run tests
npm test

# Run E2E tests
npm run test:e2e

# Build for production
npm run build
```

## Environment Variables

Create a `.env.local` file:

```env
# Required: BFF API base URL
NEXT_PUBLIC_API_BASE_URL=https://your-bff-api.com

# Optional: Enable MSW mocking (set to "true" for development)
NEXT_PUBLIC_ENABLE_MSW=true

# Optional: Timeout configuration (defaults shown)
NEXT_PUBLIC_TIMEOUT_MS=30000
NEXT_PUBLIC_RETRY_COUNT=2
NEXT_PUBLIC_RETRY_DELAY_MS=2000
```

## Architecture Overview

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (app)/              # Authenticated app routes
│   │   │   ├── dashboard/      # Main dashboard
│   │   │   ├── invoices/new/   # New sale invoice form
│   │   │   ├── notes/          # Debit/Credit note forms
│   │   │   ├── attempts/       # Submission attempt ledger
│   │   │   └── settings/       # Seller identity config
│   │   └── login/              # Authentication
│   ├── components/
│   │   ├── ui/                 # Reusable UI components
│   │   └── forms/              # Form-specific components
│   ├── features/
│   │   └── invoicing/          # Invoice domain logic
│   │       ├── schemas.ts      # Zod validation schemas
│   │       └── utils.ts        # Utility functions
│   ├── lib/
│   │   ├── api/                # API client with retry logic
│   │   ├── storage/            # IndexedDB persistence layer
│   │   └── diagnostics/        # Logging with redaction
│   ├── mocks/                  # MSW handlers
│   └── types/                  # TypeScript definitions
├── e2e/                        # Playwright E2E tests
└── vitest.config.ts            # Unit test configuration
```

## PRD Requirements Implementation

| Requirement | Implementation |
|-------------|----------------|
| **Document Types** | Three forms: Sale Invoice, Debit Note, Credit Note |
| **Invoice Ref No Uniqueness** | `isInvoiceRefNoUsed` in `src/lib/storage/indexeddb.ts` |
| **Duplicate Blocking** | If SUCCESS or UNKNOWN, block re-submission |
| **Reference Invoice Validation** | Debit/Credit notes validate via `isReferencedInvoiceValid` |
| **Timeout Retry** | 30s timeout, 2 retries on timeout only, 2s delay |
| **Attempt Ledger** | `/attempts` page with CSV export |
| **Diagnostic ID** | Generated per attempt, logged and displayed |
| **Error Classification** | `classifyError` categorizes responses |
| **Seller Identity** | Stored in IndexedDB, configured in `/settings` |

## Key Design Decisions

1. **IndexedDB for Persistence**: Offline draft saving and attempt history
2. **MSW for Development**: Mock Service Worker simulates BFF responses
3. **Zod Schema Validation**: Single source of truth for form validation
4. **TanStack Query**: Manages server state with caching
5. **Error Taxonomy**: Explicit classification for UI responses

## Testing

```bash
# Unit tests (Vitest)
npm test

# E2E tests (Playwright)
npm run test:e2e
```

## License

Private – Internal use only.
