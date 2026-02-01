/**
 * Diagnostics utilities for logging and error tracking.
 * Per PRD section 14.1, logs should be metadata-only with sensitive data redacted.
 */

/**
 * Generate a unique diagnostic ID for tracking a submission attempt
 */
export function generateDiagnosticId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 8);
  return `DIAG-${timestamp}-${random}`.toUpperCase();
}

/**
 * Fields that should be redacted in logs
 */
const SENSITIVE_FIELDS = [
  'password',
  'token',
  'bearer',
  'authorization',
  'secret',
  'key',
  'credential',
  'apikey',
  'api_key',
];

/**
 * Redact sensitive values from an object for safe logging
 */
export function redactSensitiveData<T extends Record<string, unknown>>(obj: T): T {
  const redacted = { ...obj };

  for (const key of Object.keys(redacted)) {
    const lowerKey = key.toLowerCase();

    if (SENSITIVE_FIELDS.some((field) => lowerKey.includes(field))) {
      (redacted as Record<string, unknown>)[key] = '[REDACTED]';
    } else if (typeof redacted[key] === 'object' && redacted[key] !== null) {
      (redacted as Record<string, unknown>)[key] = redactSensitiveData(
        redacted[key] as Record<string, unknown>
      );
    }
  }

  return redacted;
}

/**
 * Create a sanitized response summary for logging
 * Truncates long responses and removes sensitive data
 */
export function createResponseSummary(response: unknown, maxLength = 500): string {
  if (response === null || response === undefined) {
    return 'No response body';
  }

  let summary: string;

  if (typeof response === 'string') {
    summary = response;
  } else {
    try {
      const redacted = redactSensitiveData(response as Record<string, unknown>);
      summary = JSON.stringify(redacted);
    } catch {
      summary = String(response);
    }
  }

  if (summary.length > maxLength) {
    return summary.substring(0, maxLength) + '... [truncated]';
  }

  return summary;
}

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  diagnosticId?: string;
  data?: Record<string, unknown>;
}

/**
 * Lightweight client logger that redacts sensitive values
 */
class ClientLogger {
  private readonly isDev: boolean;

  constructor() {
    this.isDev = process.env.NEXT_PUBLIC_ENVIRONMENT === 'development';
  }

  private log(level: LogLevel, message: string, data?: Record<string, unknown>, diagnosticId?: string): void {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      diagnosticId,
      data: data ? redactSensitiveData(data) : undefined,
    };

    // In development, log to console with formatting
    if (this.isDev) {
      const prefix = diagnosticId ? `[${diagnosticId}]` : '';
      const consoleMethod = level === 'error' ? console.error :
                            level === 'warn' ? console.warn :
                            level === 'debug' ? console.debug : console.log;

      consoleMethod(`${prefix} ${message}`, entry.data ?? '');
    }

    // In production, you would send this to a logging service
    // For now, we just log to console in production too but with structured format
    if (!this.isDev) {
      console.log(JSON.stringify(entry));
    }
  }

  debug(message: string, data?: Record<string, unknown>, diagnosticId?: string): void {
    this.log('debug', message, data, diagnosticId);
  }

  info(message: string, data?: Record<string, unknown>, diagnosticId?: string): void {
    this.log('info', message, data, diagnosticId);
  }

  warn(message: string, data?: Record<string, unknown>, diagnosticId?: string): void {
    this.log('warn', message, data, diagnosticId);
  }

  error(message: string, data?: Record<string, unknown>, diagnosticId?: string): void {
    this.log('error', message, data, diagnosticId);
  }
}

export const logger = new ClientLogger();
