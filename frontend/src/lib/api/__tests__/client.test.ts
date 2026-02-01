import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiClientError, errorToOutcome } from '../client';

describe('API Error Classification', () => {
  describe('errorToOutcome', () => {
    it('should map VALIDATION category to VALIDATION_ERROR outcome', () => {
      const error = new ApiClientError({
        category: 'VALIDATION',
        message: 'Validation failed',
        diagnosticId: 'TEST-001',
        retryable: false,
      });
      expect(errorToOutcome(error)).toBe('VALIDATION_ERROR');
    });

    it('should map AUTH category to AUTH_ERROR outcome', () => {
      const error = new ApiClientError({
        category: 'AUTH',
        message: 'Authentication required',
        diagnosticId: 'TEST-002',
        retryable: false,
      });
      expect(errorToOutcome(error)).toBe('AUTH_ERROR');
    });

    it('should map DUPLICATE category to DUPLICATE_ERROR outcome', () => {
      const error = new ApiClientError({
        category: 'DUPLICATE',
        message: 'Invoice already exists',
        diagnosticId: 'TEST-003',
        retryable: false,
      });
      expect(errorToOutcome(error)).toBe('DUPLICATE_ERROR');
    });

    it('should map TRANSIENT category to TIMEOUT outcome', () => {
      const error = new ApiClientError({
        category: 'TRANSIENT',
        message: 'Request timed out',
        diagnosticId: 'TEST-004',
        retryable: true,
      });
      expect(errorToOutcome(error)).toBe('TIMEOUT');
    });

    it('should map UNKNOWN category to UNKNOWN outcome', () => {
      const error = new ApiClientError({
        category: 'UNKNOWN',
        message: 'Unknown error',
        diagnosticId: 'TEST-005',
        retryable: false,
      });
      expect(errorToOutcome(error)).toBe('UNKNOWN');
    });
  });

  describe('ApiClientError', () => {
    it('should create error with all properties', () => {
      const error = new ApiClientError({
        category: 'VALIDATION',
        message: 'Field is required',
        diagnosticId: 'TEST-006',
        httpStatus: 400,
        fieldErrors: [{ field: 'invoiceRefNo', message: 'Required' }],
        rawResponse: '{"error": "validation"}',
        retryable: false,
      });

      expect(error.category).toBe('VALIDATION');
      expect(error.message).toBe('Field is required');
      expect(error.diagnosticId).toBe('TEST-006');
      expect(error.httpStatus).toBe(400);
      expect(error.fieldErrors).toHaveLength(1);
      expect(error.retryable).toBe(false);
    });

    it('should convert to ApiError object', () => {
      const error = new ApiClientError({
        category: 'AUTH',
        message: 'Unauthorized',
        diagnosticId: 'TEST-007',
        httpStatus: 401,
        retryable: false,
      });

      const apiError = error.toApiError();
      expect(apiError.category).toBe('AUTH');
      expect(apiError.message).toBe('Unauthorized');
      expect(apiError.diagnosticId).toBe('TEST-007');
    });
  });
});
