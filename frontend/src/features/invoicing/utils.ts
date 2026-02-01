import type { InvoiceDocument, InvoiceItem, AttemptEntry, DocumentType } from '@/types';
import type { SubmitInvoiceRequest, SubmitInvoiceItem } from '@/types/api';

/**
 * Suggest next invoiceRefNo based on last successful submission
 * Algorithm per PRD section 9.3:
 * - If prior ref has trailing digits: increment trailing integer by 1; preserve leading zeros width
 * - If no trailing digits: provide no suggestion
 *
 * @param lastRefNo - The last successfully submitted invoiceRefNo
 * @returns Suggested next invoiceRefNo or null if no suggestion possible
 */
export function suggestNextInvoiceRefNo(lastRefNo: string | null): string | null {
  if (!lastRefNo) return null;

  // Match trailing digits
  const match = lastRefNo.match(/^(.*?)(\d+)$/);
  if (!match) return null;

  const prefix = match[1];
  const numericPart = match[2];
  const nextNumber = parseInt(numericPart, 10) + 1;

  // Preserve leading zeros width
  const paddedNumber = nextNumber.toString().padStart(numericPart.length, '0');

  return `${prefix}${paddedNumber}`;
}

/**
 * Map InvoiceDocument to SubmitInvoiceRequest for API
 */
export function mapDocumentToRequest(doc: InvoiceDocument): SubmitInvoiceRequest {
  return {
    invoiceType: doc.invoiceType,
    invoiceDate: doc.invoiceDate,
    sellerNTNCNIC: doc.sellerNTNCNIC,
    sellerBusinessName: doc.sellerBusinessName,
    sellerProvince: doc.sellerProvince,
    sellerAddress: doc.sellerAddress,
    buyerNTNCNIC: doc.buyerNTNCNIC,
    buyerBusinessName: doc.buyerBusinessName,
    buyerProvince: doc.buyerProvince,
    buyerAddress: doc.buyerAddress,
    buyerRegistrationType: doc.buyerRegistrationType,
    invoiceRefNo: doc.invoiceRefNo,
    scenarioId: doc.scenarioId,
    items: doc.items.map(mapItemToRequest),
  };
}

/**
 * Map InvoiceItem to SubmitInvoiceItem for API
 */
function mapItemToRequest(item: InvoiceItem): SubmitInvoiceItem {
  return {
    hsCode: item.hsCode,
    productDescription: item.productDescription,
    rate: item.rate,
    uoM: item.uoM,
    quantity: item.quantity,
    totalValues: item.totalValues,
    valueSalesExcludingST: item.valueSalesExcludingST,
    fixedNotifiedValueOrRetailPrice: item.fixedNotifiedValueOrRetailPrice,
    salesTaxApplicable: item.salesTaxApplicable,
    salesTaxWithheldAtSource: item.salesTaxWithheldAtSource,
    extraTax: item.extraTax,
    furtherTax: item.furtherTax,
    sroScheduleNo: item.sroScheduleNo,
    fedPayable: item.fedPayable,
    discount: item.discount,
    saleType: item.saleType,
    sroItemSerialNo: item.sroItemSerialNo,
  };
}

/**
 * Generate CSV content from attempt entries
 */
export function generateAttemptsCsv(attempts: AttemptEntry[]): string {
  const headers = [
    'Timestamp',
    'Invoice Ref No',
    'Document Type',
    'Seller NTN',
    'Attempt #',
    'Outcome',
    'HTTP Status',
    'Duration (ms)',
    'Diagnostic ID',
    'Response Summary',
  ];

  const rows = attempts.map((a) => [
    a.timestamp,
    a.invoiceRefNo,
    a.documentType,
    a.sellerNTNCNIC,
    a.attemptNumber.toString(),
    a.outcome,
    a.httpStatus?.toString() ?? '',
    a.durationMs?.toString() ?? '',
    a.diagnosticId,
    // Escape quotes and wrap in quotes for CSV
    `"${(a.responseSummary ?? '').replace(/"/g, '""')}"`,
  ]);

  const csvContent = [
    headers.join(','),
    ...rows.map((row) => row.join(',')),
  ].join('\n');

  return csvContent;
}

/**
 * Download a string as a file
 */
export function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Format date for display
 */
export function formatDate(dateString: string): string {
  try {
    return new Date(dateString).toLocaleDateString('en-PK', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
}

/**
 * Format timestamp for display
 */
export function formatTimestamp(timestamp: string): string {
  try {
    return new Date(timestamp).toLocaleString('en-PK', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return timestamp;
  }
}

/**
 * Get document type display label
 */
export function getDocumentTypeLabel(type: DocumentType): string {
  switch (type) {
    case 'SALE_INVOICE':
      return 'Sale Invoice';
    case 'DEBIT_NOTE':
      return 'Debit Note';
    case 'CREDIT_NOTE':
      return 'Credit Note';
    default:
      return type;
  }
}

/**
 * Calculate item total
 */
export function calculateItemTotal(item: Partial<InvoiceItem>): number {
  const quantity = item.quantity ?? 0;
  const unitValue = item.valueSalesExcludingST ?? 0;
  const tax = item.salesTaxApplicable ?? 0;
  const discount = item.discount ?? 0;

  return quantity * unitValue + tax - discount;
}
