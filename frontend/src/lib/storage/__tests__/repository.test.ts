import { describe, it, expect, beforeEach, vi } from 'vitest';
import { deriveDocumentStatus } from '../repository';
import type { AttemptEntry } from '@/types';

describe('Storage Repository', () => {
  describe('deriveDocumentStatus', () => {
    const createAttempt = (
      outcome: AttemptEntry['outcome'],
      timestamp: string
    ): AttemptEntry => ({
      id: crypto.randomUUID(),
      documentId: 'doc-1',
      invoiceRefNo: 'INV-001',
      sellerNTNCNIC: '1234567',
      documentType: 'SALE_INVOICE',
      attemptNumber: 1,
      timestamp,
      endpoint: '/api/bff/invoices/submit',
      outcome,
      diagnosticId: 'DIAG-001',
    });

    it('should return DRAFT when no attempts exist', () => {
      expect(deriveDocumentStatus([])).toBe('DRAFT');
    });

    it('should return SUCCESS when latest attempt is successful', () => {
      const attempts = [
        createAttempt('VALIDATION_ERROR', '2024-01-01T10:00:00Z'),
        createAttempt('SUCCESS', '2024-01-01T11:00:00Z'),
      ];
      expect(deriveDocumentStatus(attempts)).toBe('SUCCESS');
    });

    it('should return FAILED for validation errors', () => {
      const attempts = [createAttempt('VALIDATION_ERROR', '2024-01-01T10:00:00Z')];
      expect(deriveDocumentStatus(attempts)).toBe('FAILED');
    });

    it('should return FAILED for auth errors', () => {
      const attempts = [createAttempt('AUTH_ERROR', '2024-01-01T10:00:00Z')];
      expect(deriveDocumentStatus(attempts)).toBe('FAILED');
    });

    it('should return FAILED for duplicate errors', () => {
      const attempts = [createAttempt('DUPLICATE_ERROR', '2024-01-01T10:00:00Z')];
      expect(deriveDocumentStatus(attempts)).toBe('FAILED');
    });

    it('should return UNKNOWN for timeout', () => {
      const attempts = [createAttempt('TIMEOUT', '2024-01-01T10:00:00Z')];
      expect(deriveDocumentStatus(attempts)).toBe('UNKNOWN');
    });

    it('should return UNKNOWN for unknown outcome', () => {
      const attempts = [createAttempt('UNKNOWN', '2024-01-01T10:00:00Z')];
      expect(deriveDocumentStatus(attempts)).toBe('UNKNOWN');
    });

    it('should use the most recent attempt when multiple exist', () => {
      const attempts = [
        createAttempt('SUCCESS', '2024-01-01T09:00:00Z'),
        createAttempt('TIMEOUT', '2024-01-01T11:00:00Z'),
        createAttempt('VALIDATION_ERROR', '2024-01-01T10:00:00Z'),
      ];
      // Latest is TIMEOUT at 11:00
      expect(deriveDocumentStatus(attempts)).toBe('UNKNOWN');
    });
  });
});
