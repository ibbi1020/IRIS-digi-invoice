import { http, HttpResponse, delay } from 'msw';

// Track submitted invoices for duplicate detection
const submittedInvoices = new Map<string, { timestamp: string; status: string }>();

/**
 * MSW handlers for mocking the BFF API
 */
export const handlers = [
  // Health check
  http.get('/api/bff/health', () => {
    return HttpResponse.json({ status: 'ok', timestamp: new Date().toISOString() });
  }),

  // Submit invoice
  http.post('/api/bff/invoices/submit', async ({ request }) => {
    const body = await request.json() as { invoiceRefNo?: string; sellerNTNCNIC?: string };
    const diagnosticId = request.headers.get('X-Diagnostic-Id') ?? 'MOCK-UNKNOWN';

    // Simulate network latency
    await delay(500 + Math.random() * 1000);

    const invoiceRefNo = body.invoiceRefNo;
    const sellerNTN = body.sellerNTNCNIC;

    // Simulate different scenarios based on invoiceRefNo patterns
    // This allows testing various outcomes

    // Timeout simulation: refs ending with "-TIMEOUT"
    if (invoiceRefNo?.endsWith('-TIMEOUT')) {
      await delay(35000); // Exceed the 30s timeout
      return HttpResponse.json({ success: true });
    }

    // Validation error: refs ending with "-INVALID"
    if (invoiceRefNo?.endsWith('-INVALID')) {
      return HttpResponse.json(
        {
          success: false,
          error: {
            category: 'VALIDATION',
            message: 'Validation failed',
            diagnosticId,
            fieldErrors: [
              { field: 'buyerNTNCNIC', message: 'Invalid NTN format' },
              { field: 'items[0].hsCode', message: 'Invalid HS code' },
            ],
          },
        },
        { status: 400 }
      );
    }

    // Auth error: refs ending with "-AUTH"
    if (invoiceRefNo?.endsWith('-AUTH')) {
      return HttpResponse.json(
        {
          success: false,
          error: {
            category: 'AUTH',
            message: 'Authentication required',
            diagnosticId,
          },
        },
        { status: 401 }
      );
    }

    // Duplicate check
    const key = `${sellerNTN}:${invoiceRefNo}`;
    if (submittedInvoices.has(key)) {
      return HttpResponse.json(
        {
          success: false,
          error: {
            category: 'DUPLICATE',
            message: 'Invoice reference number already exists',
            diagnosticId,
          },
        },
        { status: 409 }
      );
    }

    // Success - record the submission
    submittedInvoices.set(key, {
      timestamp: new Date().toISOString(),
      status: 'SUCCESS',
    });

    return HttpResponse.json({
      success: true,
      invoiceRefNo,
      message: 'Invoice submitted successfully',
      irisReference: `IRIS-${Date.now()}`,
      timestamp: new Date().toISOString(),
    });
  }),
];

/**
 * Reset mock state (useful for tests)
 */
export function resetMockState() {
  submittedInvoices.clear();
}
