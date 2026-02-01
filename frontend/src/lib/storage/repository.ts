import type {
  InvoiceDocument,
  AttemptEntry,
  DocumentType,
  DocumentStatus,
  DocumentWithStatus,
  SellerIdentity,
} from '@/types';

/**
 * Storage repository interface.
 * Abstracts persistence layer so implementation can be swapped (IndexedDB -> Backend API).
 */
export interface StorageRepository {
  // Documents
  saveDocument(doc: InvoiceDocument): Promise<void>;
  getDocument(id: string): Promise<InvoiceDocument | null>;
  getDocumentByRefNo(invoiceRefNo: string, sellerNTN: string): Promise<InvoiceDocument | null>;
  getAllDocuments(sellerNTN?: string): Promise<InvoiceDocument[]>;
  deleteDocument(id: string): Promise<void>;

  // Attempts
  saveAttempt(attempt: AttemptEntry): Promise<void>;
  getAttemptsByDocument(documentId: string): Promise<AttemptEntry[]>;
  getAttemptsByRefNo(invoiceRefNo: string, sellerNTN: string): Promise<AttemptEntry[]>;
  getAllAttempts(sellerNTN?: string): Promise<AttemptEntry[]>;
  getLatestAttemptByRefNo(invoiceRefNo: string, sellerNTN: string): Promise<AttemptEntry | null>;

  // Seller Identity
  saveSellerIdentity(identity: SellerIdentity): Promise<void>;
  getSellerIdentity(): Promise<SellerIdentity | null>;

  // Uniqueness checks
  isInvoiceRefNoUsed(invoiceRefNo: string, sellerNTN: string): Promise<{
    used: boolean;
    status: DocumentStatus | null;
  }>;

  // Get last successful ref for suggestion
  getLastSuccessfulRefNo(sellerNTN: string): Promise<string | null>;

  // Check if referenced invoice exists and is successful (for debit/credit notes)
  isReferencedInvoiceValid(invoiceRefNo: string, sellerNTN: string): Promise<{
    valid: boolean;
    reason?: string;
  }>;
}

/**
 * Derive document status from attempts
 */
export function deriveDocumentStatus(attempts: AttemptEntry[]): DocumentStatus {
  if (attempts.length === 0) return 'DRAFT';

  // Sort by timestamp descending to get latest
  const sorted = [...attempts].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  const latest = sorted[0];

  switch (latest.outcome) {
    case 'SUCCESS':
      return 'SUCCESS';
    case 'VALIDATION_ERROR':
    case 'AUTH_ERROR':
    case 'DUPLICATE_ERROR':
      return 'FAILED';
    case 'TIMEOUT':
    case 'UNKNOWN':
      return 'UNKNOWN';
    default:
      return 'UNKNOWN';
  }
}

/**
 * Add status to document based on attempts
 */
export function enrichDocumentWithStatus(
  doc: InvoiceDocument,
  attempts: AttemptEntry[]
): DocumentWithStatus {
  const docAttempts = attempts.filter((a) => a.documentId === doc.id);
  const sorted = [...docAttempts].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  return {
    ...doc,
    status: deriveDocumentStatus(docAttempts),
    lastAttempt: sorted[0],
  };
}
