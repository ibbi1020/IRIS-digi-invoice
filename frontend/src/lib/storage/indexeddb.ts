import { openDB, type IDBPDatabase, type DBSchema } from 'idb';
import type {
  InvoiceDocument,
  AttemptEntry,
  DocumentStatus,
  SellerIdentity,
} from '@/types';
import { type StorageRepository, deriveDocumentStatus } from './repository';

/**
 * IndexedDB schema definition
 */
interface IrisDBSchema extends DBSchema {
  documents: {
    key: string;
    value: InvoiceDocument;
    indexes: {
      'by-refno-seller': [string, string];
      'by-seller': string;
      'by-type': string;
    };
  };
  attempts: {
    key: string;
    value: AttemptEntry;
    indexes: {
      'by-document': string;
      'by-refno-seller': [string, string];
      'by-seller': string;
      'by-timestamp': string;
    };
  };
  settings: {
    key: string;
    value: {
      id: string;
      data: SellerIdentity;
    };
  };
}

const DB_NAME = 'iris-invoicing';
const DB_VERSION = 1;

/**
 * Initialize the IndexedDB database
 */
async function initDB(): Promise<IDBPDatabase<IrisDBSchema>> {
  return openDB<IrisDBSchema>(DB_NAME, DB_VERSION, {
    upgrade(db) {
      // Documents store
      if (!db.objectStoreNames.contains('documents')) {
        const docStore = db.createObjectStore('documents', { keyPath: 'id' });
        docStore.createIndex('by-refno-seller', ['invoiceRefNo', 'sellerNTNCNIC']);
        docStore.createIndex('by-seller', 'sellerNTNCNIC');
        docStore.createIndex('by-type', 'documentType');
      }

      // Attempts store
      if (!db.objectStoreNames.contains('attempts')) {
        const attemptStore = db.createObjectStore('attempts', { keyPath: 'id' });
        attemptStore.createIndex('by-document', 'documentId');
        attemptStore.createIndex('by-refno-seller', ['invoiceRefNo', 'sellerNTNCNIC']);
        attemptStore.createIndex('by-seller', 'sellerNTNCNIC');
        attemptStore.createIndex('by-timestamp', 'timestamp');
      }

      // Settings store
      if (!db.objectStoreNames.contains('settings')) {
        db.createObjectStore('settings', { keyPath: 'id' });
      }
    },
  });
}

let dbPromise: Promise<IDBPDatabase<IrisDBSchema>> | null = null;

function getDB(): Promise<IDBPDatabase<IrisDBSchema>> {
  if (!dbPromise) {
    dbPromise = initDB();
  }
  return dbPromise;
}

/**
 * IndexedDB implementation of StorageRepository
 */
export class IndexedDBRepository implements StorageRepository {
  // Documents
  async saveDocument(doc: InvoiceDocument): Promise<void> {
    const db = await getDB();
    await db.put('documents', doc);
  }

  async getDocument(id: string): Promise<InvoiceDocument | null> {
    const db = await getDB();
    return (await db.get('documents', id)) ?? null;
  }

  async getDocumentByRefNo(
    invoiceRefNo: string,
    sellerNTN: string
  ): Promise<InvoiceDocument | null> {
    const db = await getDB();
    return (await db.getFromIndex('documents', 'by-refno-seller', [invoiceRefNo, sellerNTN])) ?? null;
  }

  async getAllDocuments(sellerNTN?: string): Promise<InvoiceDocument[]> {
    const db = await getDB();
    if (sellerNTN) {
      return db.getAllFromIndex('documents', 'by-seller', sellerNTN);
    }
    return db.getAll('documents');
  }

  async deleteDocument(id: string): Promise<void> {
    const db = await getDB();
    await db.delete('documents', id);
  }

  // Attempts
  async saveAttempt(attempt: AttemptEntry): Promise<void> {
    const db = await getDB();
    await db.put('attempts', attempt);
  }

  async getAttemptsByDocument(documentId: string): Promise<AttemptEntry[]> {
    const db = await getDB();
    return db.getAllFromIndex('attempts', 'by-document', documentId);
  }

  async getAttemptsByRefNo(invoiceRefNo: string, sellerNTN: string): Promise<AttemptEntry[]> {
    const db = await getDB();
    return db.getAllFromIndex('attempts', 'by-refno-seller', [invoiceRefNo, sellerNTN]);
  }

  async getAllAttempts(sellerNTN?: string): Promise<AttemptEntry[]> {
    const db = await getDB();
    let attempts: AttemptEntry[];
    if (sellerNTN) {
      attempts = await db.getAllFromIndex('attempts', 'by-seller', sellerNTN);
    } else {
      attempts = await db.getAll('attempts');
    }
    // Sort by timestamp descending
    return attempts.sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }

  async getLatestAttemptByRefNo(
    invoiceRefNo: string,
    sellerNTN: string
  ): Promise<AttemptEntry | null> {
    const attempts = await this.getAttemptsByRefNo(invoiceRefNo, sellerNTN);
    if (attempts.length === 0) return null;

    return attempts.sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )[0];
  }

  // Seller Identity
  async saveSellerIdentity(identity: SellerIdentity): Promise<void> {
    const db = await getDB();
    await db.put('settings', { id: 'seller-identity', data: identity });
  }

  async getSellerIdentity(): Promise<SellerIdentity | null> {
    const db = await getDB();
    const result = await db.get('settings', 'seller-identity');
    return result?.data ?? null;
  }

  // Uniqueness checks
  async isInvoiceRefNoUsed(
    invoiceRefNo: string,
    sellerNTN: string
  ): Promise<{ used: boolean; status: DocumentStatus | null }> {
    const attempts = await this.getAttemptsByRefNo(invoiceRefNo, sellerNTN);

    if (attempts.length === 0) {
      return { used: false, status: null };
    }

    const status = deriveDocumentStatus(attempts);
    return { used: true, status };
  }

  async getLastSuccessfulRefNo(sellerNTN: string): Promise<string | null> {
    const db = await getDB();
    const attempts = await db.getAllFromIndex('attempts', 'by-seller', sellerNTN);

    // Filter to successful attempts and sort by timestamp descending
    const successful = attempts
      .filter((a) => a.outcome === 'SUCCESS')
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    return successful[0]?.invoiceRefNo ?? null;
  }

  async isReferencedInvoiceValid(
    invoiceRefNo: string,
    sellerNTN: string
  ): Promise<{ valid: boolean; reason?: string }> {
    // Check if the referenced invoice exists and is in SUCCESS state
    const { used, status } = await this.isInvoiceRefNoUsed(invoiceRefNo, sellerNTN);

    if (!used) {
      return {
        valid: false,
        reason: `Referenced invoice "${invoiceRefNo}" not found.`,
      };
    }

    if (status !== 'SUCCESS') {
      return {
        valid: false,
        reason: `Referenced invoice "${invoiceRefNo}" is not in a successful state (current: ${status}).`,
      };
    }

    // Also verify the document type is SALE_INVOICE
    const doc = await this.getDocumentByRefNo(invoiceRefNo, sellerNTN);
    if (doc && doc.documentType !== 'SALE_INVOICE') {
      return {
        valid: false,
        reason: `Referenced document "${invoiceRefNo}" is not a Sale Invoice.`,
      };
    }

    return { valid: true };
  }
}

/**
 * Singleton instance
 */
let repository: StorageRepository | null = null;

export function getStorageRepository(): StorageRepository {
  if (!repository) {
    repository = new IndexedDBRepository();
  }
  return repository;
}
