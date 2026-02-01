/**
 * Document Types supported by IRIS/FBR Digital Invoicing
 */
export type DocumentType = 'SALE_INVOICE' | 'DEBIT_NOTE' | 'CREDIT_NOTE';

/**
 * Maps DocumentType to IRIS/FBR API invoiceType values
 */
export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  SALE_INVOICE: 'Sale Invoice',
  DEBIT_NOTE: 'Debit Note',
  CREDIT_NOTE: 'Credit Note',
};

/**
 * Buyer registration types
 */
export type BuyerRegistrationType = 'Registered' | 'Unregistered';

/**
 * Sale types for line items
 */
export type SaleType = 'Local' | 'Export' | 'Zero-Rated';

/**
 * Attempt outcome categories per PRD section 8
 */
export type AttemptOutcome =
  | 'SUCCESS'
  | 'VALIDATION_ERROR'
  | 'AUTH_ERROR'
  | 'DUPLICATE_ERROR'
  | 'TIMEOUT'
  | 'UNKNOWN';

/**
 * Invoice line item
 */
export interface InvoiceItem {
  id: string;
  hsCode: string;
  productDescription: string;
  rate: string;
  uoM: string;
  quantity: number;
  totalValues: number;
  valueSalesExcludingST: number;
  fixedNotifiedValueOrRetailPrice: number;
  salesTaxApplicable: number;
  salesTaxWithheldAtSource: number;
  extraTax: string;
  furtherTax: number;
  sroScheduleNo: string;
  fedPayable: number;
  discount: number;
  saleType: SaleType | '';
  sroItemSerialNo: string;
}

/**
 * Seller identity/configuration stored locally
 */
export interface SellerIdentity {
  sellerNTNCNIC: string;
  sellerBusinessName: string;
  sellerProvince: string;
  sellerAddress: string;
}

/**
 * Invoice document (canonical portal model)
 * Aligns with PRD section 11.1
 */
export interface InvoiceDocument {
  // Internal metadata
  id: string;
  createdAt: string;
  updatedAt: string;
  documentType: DocumentType;

  // Reference for debit/credit notes
  referencedInvoiceRefNo?: string;

  // IRIS/FBR fields
  invoiceType: string;
  invoiceDate: string;
  invoiceRefNo: string;
  scenarioId: string;

  // Seller info
  sellerNTNCNIC: string;
  sellerBusinessName: string;
  sellerProvince: string;
  sellerAddress: string;

  // Buyer info
  buyerNTNCNIC: string;
  buyerBusinessName: string;
  buyerProvince: string;
  buyerAddress: string;
  buyerRegistrationType: BuyerRegistrationType;

  // Line items
  items: InvoiceItem[];
}

/**
 * Attempt ledger entry (append-only)
 * Per PRD section 14.1
 */
export interface AttemptEntry {
  id: string;
  documentId: string;
  invoiceRefNo: string;
  sellerNTNCNIC: string;
  documentType: DocumentType;
  attemptNumber: number;
  timestamp: string;
  endpoint: string;
  outcome: AttemptOutcome;
  diagnosticId: string;
  httpStatus?: number;
  responseSummary?: string;
  errorDetails?: string;
  durationMs?: number;
}

/**
 * Document submission status derived from attempts
 */
export type DocumentStatus =
  | 'DRAFT'
  | 'PENDING'
  | 'SUCCESS'
  | 'FAILED'
  | 'UNKNOWN';

/**
 * Document with computed status
 */
export interface DocumentWithStatus extends InvoiceDocument {
  status: DocumentStatus;
  lastAttempt?: AttemptEntry;
}

/**
 * Draft document (before submission)
 */
export interface DraftDocument extends Omit<InvoiceDocument, 'id' | 'createdAt' | 'updatedAt'> {
  id?: string;
}
