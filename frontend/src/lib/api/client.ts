import { env } from '@/lib/env';
import { generateDiagnosticId, createResponseSummary, logger } from '@/lib/diagnostics';
import type {
  ApiError,
  ApiErrorCategory,
  SubmitInvoiceRequest,
  SubmitResponse,
  FieldError,
} from '@/types/api';
import type { AttemptOutcome } from '@/types';

/**
 * Custom error class for API errors
 */
export class ApiClientError extends Error {
  readonly category: ApiErrorCategory;
  readonly diagnosticId: string;
  readonly httpStatus?: number;
  readonly fieldErrors?: FieldError[];
  readonly rawResponse?: string;
  readonly retryable: boolean;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiClientError';
    this.category = error.category;
    this.diagnosticId = error.diagnosticId;
    this.httpStatus = error.httpStatus;
    this.fieldErrors = error.fieldErrors;
    this.rawResponse = error.rawResponse;
    this.retryable = error.retryable;
  }

  toApiError(): ApiError {
    return {
      category: this.category,
      message: this.message,
      diagnosticId: this.diagnosticId,
      httpStatus: this.httpStatus,
      fieldErrors: this.fieldErrors,
      rawResponse: this.rawResponse,
      retryable: this.retryable,
    };
  }
}

/**
 * Timeout wrapper that rejects after specified duration
 */
function withTimeout<T>(promise: Promise<T>, ms: number, diagnosticId: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(
        new ApiClientError({
          category: 'TRANSIENT',
          message: `Request timed out after ${ms}ms`,
          diagnosticId,
          retryable: true,
        })
      );
    }, ms);

    promise
      .then((result) => {
        clearTimeout(timeoutId);
        resolve(result);
      })
      .catch((error) => {
        clearTimeout(timeoutId);
        reject(error);
      });
  });
}

/**
 * Classify HTTP status and response into error category
 */
function classifyError(
  status: number,
  responseBody: unknown,
  diagnosticId: string
): ApiClientError {
  const rawResponse = createResponseSummary(responseBody);

  // Auth errors
  if (status === 401 || status === 403) {
    return new ApiClientError({
      category: 'AUTH',
      message: status === 401 ? 'Authentication required' : 'Access forbidden',
      diagnosticId,
      httpStatus: status,
      rawResponse,
      retryable: false,
    });
  }

  // Validation errors
  if (status === 400 || status === 422) {
    const fieldErrors = extractFieldErrors(responseBody);
    return new ApiClientError({
      category: 'VALIDATION',
      message: 'Validation failed',
      diagnosticId,
      httpStatus: status,
      fieldErrors,
      rawResponse,
      retryable: false,
    });
  }

  // Duplicate (usually 409 Conflict, but may vary by IRIS/FBR)
  if (status === 409) {
    return new ApiClientError({
      category: 'DUPLICATE',
      message: 'Invoice reference already exists',
      diagnosticId,
      httpStatus: status,
      rawResponse,
      retryable: false,
    });
  }

  // Rate limiting (if IRIS/FBR uses it)
  if (status === 429) {
    return new ApiClientError({
      category: 'TRANSIENT',
      message: 'Rate limit exceeded. Please try again later.',
      diagnosticId,
      httpStatus: status,
      rawResponse,
      retryable: false, // Per PRD, no auto-retry for rate limits
    });
  }

  // Server errors
  if (status >= 500) {
    return new ApiClientError({
      category: 'UNKNOWN',
      message: 'Server error occurred',
      diagnosticId,
      httpStatus: status,
      rawResponse,
      retryable: false, // Per PRD, only timeout triggers retry
    });
  }

  // Unknown
  return new ApiClientError({
    category: 'UNKNOWN',
    message: 'An unexpected error occurred',
    diagnosticId,
    httpStatus: status,
    rawResponse,
    retryable: false,
  });
}

/**
 * Extract field errors from API response
 */
function extractFieldErrors(responseBody: unknown): FieldError[] | undefined {
  if (!responseBody || typeof responseBody !== 'object') return undefined;

  const body = responseBody as Record<string, unknown>;

  // Try common error response formats
  if (Array.isArray(body.errors)) {
    return body.errors.map((err: unknown) => {
      if (typeof err === 'object' && err !== null) {
        const e = err as Record<string, unknown>;
        return {
          field: String(e.field ?? e.path ?? 'unknown'),
          message: String(e.message ?? e.error ?? 'Unknown error'),
          code: e.code ? String(e.code) : undefined,
        };
      }
      return { field: 'unknown', message: String(err) };
    });
  }

  if (body.fieldErrors && typeof body.fieldErrors === 'object') {
    return Object.entries(body.fieldErrors as Record<string, string>).map(
      ([field, message]) => ({ field, message })
    );
  }

  return undefined;
}

/**
 * Map ApiClientError to AttemptOutcome
 */
export function errorToOutcome(error: ApiClientError): AttemptOutcome {
  switch (error.category) {
    case 'VALIDATION':
      return 'VALIDATION_ERROR';
    case 'AUTH':
      return 'AUTH_ERROR';
    case 'DUPLICATE':
      return 'DUPLICATE_ERROR';
    case 'TRANSIENT':
      return 'TIMEOUT';
    case 'UNKNOWN':
    default:
      return 'UNKNOWN';
  }
}

/**
 * Delay for specified milliseconds
 */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export interface SubmitAttemptResult {
  success: boolean;
  response?: SubmitResponse;
  error?: ApiClientError;
  attemptNumber: number;
  diagnosticId: string;
  durationMs: number;
}

/**
 * Submit invoice to BFF with retry logic per PRD section 10
 * - Timeout: 30s (configurable)
 * - Auto retry: 2 times on timeout only
 * - Delay: 2s between retries
 */
export async function submitInvoice(
  request: SubmitInvoiceRequest,
  onAttemptComplete?: (result: SubmitAttemptResult) => void
): Promise<SubmitAttemptResult> {
  const maxAttempts = 1 + env.NEXT_PUBLIC_TIMEOUT_RETRY_COUNT;
  const timeoutMs = env.NEXT_PUBLIC_REQUEST_TIMEOUT_MS;
  const retryDelayMs = env.NEXT_PUBLIC_RETRY_DELAY_MS;

  let lastResult: SubmitAttemptResult | null = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const diagnosticId = generateDiagnosticId();
    const startTime = Date.now();

    logger.info(`Starting submit attempt`, {
      attemptNumber: attempt,
      invoiceRefNo: request.invoiceRefNo,
      maxAttempts,
    }, diagnosticId);

    try {
      const response = await withTimeout(
        fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/invoices/submit`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Diagnostic-Id': diagnosticId,
          },
          body: JSON.stringify(request),
        }),
        timeoutMs,
        diagnosticId
      );

      const durationMs = Date.now() - startTime;
      const responseBody = await response.json().catch(() => null);

      if (response.ok) {
        const successResponse: SubmitResponse = {
          success: true,
          invoiceRefNo: request.invoiceRefNo,
          timestamp: new Date().toISOString(),
          ...(responseBody as object),
        };

        lastResult = {
          success: true,
          response: successResponse,
          attemptNumber: attempt,
          diagnosticId,
          durationMs,
        };

        logger.info('Submit succeeded', {
          attemptNumber: attempt,
          durationMs,
        }, diagnosticId);

        onAttemptComplete?.(lastResult);
        return lastResult;
      }

      // Non-success response
      const error = classifyError(response.status, responseBody, diagnosticId);

      lastResult = {
        success: false,
        error,
        attemptNumber: attempt,
        diagnosticId,
        durationMs,
      };

      logger.warn('Submit failed', {
        attemptNumber: attempt,
        category: error.category,
        httpStatus: error.httpStatus,
        durationMs,
      }, diagnosticId);

      onAttemptComplete?.(lastResult);

      // Don't retry non-transient errors
      if (!error.retryable) {
        return lastResult;
      }
    } catch (err) {
      const durationMs = Date.now() - startTime;

      // Handle timeout errors (from our wrapper or network)
      const error =
        err instanceof ApiClientError
          ? err
          : new ApiClientError({
              category: 'TRANSIENT',
              message: err instanceof Error ? err.message : 'Network error',
              diagnosticId,
              retryable: true,
            });

      lastResult = {
        success: false,
        error,
        attemptNumber: attempt,
        diagnosticId,
        durationMs,
      };

      logger.warn('Submit attempt failed (will retry if timeout)', {
        attemptNumber: attempt,
        category: error.category,
        message: error.message,
        durationMs,
      }, diagnosticId);

      onAttemptComplete?.(lastResult);

      // Only retry on timeout
      if (error.category !== 'TRANSIENT' || attempt >= maxAttempts) {
        return lastResult;
      }

      // Delay before retry
      logger.info(`Waiting ${retryDelayMs}ms before retry`, {
        nextAttempt: attempt + 1,
      }, diagnosticId);

      await delay(retryDelayMs);
    }
  }

  // Should not reach here, but return last result just in case
  return lastResult!;
}

/**
 * Health check for BFF
 */
export async function checkBffHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/health`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
}
