import { describe, it, expect } from 'vitest';
import { suggestNextInvoiceRefNo } from '../utils';

describe('suggestNextInvoiceRefNo', () => {
  it('should return null for null input', () => {
    expect(suggestNextInvoiceRefNo(null)).toBeNull();
  });

  it('should return null for empty string', () => {
    expect(suggestNextInvoiceRefNo('')).toBeNull();
  });

  it('should return null for strings without trailing digits', () => {
    expect(suggestNextInvoiceRefNo('INV-A')).toBeNull();
    expect(suggestNextInvoiceRefNo('ABC')).toBeNull();
    expect(suggestNextInvoiceRefNo('invoice')).toBeNull();
  });

  it('should increment simple numeric references', () => {
    expect(suggestNextInvoiceRefNo('1005')).toBe('1006');
    expect(suggestNextInvoiceRefNo('100')).toBe('101');
    expect(suggestNextInvoiceRefNo('1')).toBe('2');
    expect(suggestNextInvoiceRefNo('999')).toBe('1000');
  });

  it('should preserve leading zeros width', () => {
    expect(suggestNextInvoiceRefNo('0009')).toBe('0010');
    expect(suggestNextInvoiceRefNo('001')).toBe('002');
    expect(suggestNextInvoiceRefNo('0001')).toBe('0002');
    expect(suggestNextInvoiceRefNo('0099')).toBe('0100');
  });

  it('should handle prefixed references', () => {
    expect(suggestNextInvoiceRefNo('INV-0009')).toBe('INV-0010');
    expect(suggestNextInvoiceRefNo('INV-1005')).toBe('INV-1006');
    expect(suggestNextInvoiceRefNo('SI-2024-0001')).toBe('SI-2024-0002');
    expect(suggestNextInvoiceRefNo('ABC123')).toBe('ABC124');
  });

  it('should handle overflow from leading zeros', () => {
    // When incrementing causes more digits, leading zeros are reduced
    expect(suggestNextInvoiceRefNo('INV-099')).toBe('INV-100');
    expect(suggestNextInvoiceRefNo('INV-0099')).toBe('INV-0100');
    expect(suggestNextInvoiceRefNo('INV-9999')).toBe('INV-10000');
  });
});
