import { z } from 'zod';
import type { DocumentType, BuyerRegistrationType, SaleType } from '@/types';

/**
 * Zod schema for invoice line item
 */
export const invoiceItemSchema = z.object({
  id: z.string().min(1),
  hsCode: z.string().min(1, 'HS Code is required'),
  productDescription: z.string().min(1, 'Product description is required'),
  rate: z.string().min(1, 'Tax rate is required'),
  uoM: z.string().min(1, 'Unit of measure is required'),
  quantity: z.number().min(0, 'Quantity must be non-negative'),
  totalValues: z.number().min(0, 'Total value must be non-negative'),
  valueSalesExcludingST: z.number().min(0, 'Value excluding ST must be non-negative'),
  fixedNotifiedValueOrRetailPrice: z.number().min(0, 'Fixed/notified value must be non-negative'),
  salesTaxApplicable: z.number().min(0, 'Sales tax must be non-negative'),
  salesTaxWithheldAtSource: z.number().min(0, 'Sales tax withheld must be non-negative'),
  extraTax: z.string(),
  furtherTax: z.number().min(0, 'Further tax must be non-negative'),
  sroScheduleNo: z.string(),
  fedPayable: z.number().min(0, 'FED payable must be non-negative'),
  discount: z.number().min(0, 'Discount must be non-negative'),
  saleType: z.enum(['Local', 'Export', 'Zero-Rated', '']),
  sroItemSerialNo: z.string(),
});

export type InvoiceItemFormData = z.infer<typeof invoiceItemSchema>;

/**
 * Zod schema for seller identity
 */
export const sellerIdentitySchema = z.object({
  sellerNTNCNIC: z
    .string()
    .min(1, 'Seller NTN/CNIC is required')
    .regex(/^\d{7,13}$/, 'NTN/CNIC must be 7-13 digits'),
  sellerBusinessName: z.string().min(1, 'Business name is required'),
  sellerProvince: z.string().min(1, 'Province is required'),
  sellerAddress: z.string().min(1, 'Address is required'),
});

export type SellerIdentityFormData = z.infer<typeof sellerIdentitySchema>;

/**
 * Zod schema for buyer information
 */
export const buyerInfoSchema = z.object({
  buyerNTNCNIC: z
    .string()
    .min(1, 'Buyer NTN/CNIC is required')
    .regex(/^\d{7,13}$/, 'NTN/CNIC must be 7-13 digits'),
  buyerBusinessName: z.string().min(1, 'Business name is required'),
  buyerProvince: z.string().min(1, 'Province is required'),
  buyerAddress: z.string().min(1, 'Address is required'),
  buyerRegistrationType: z.enum(['Registered', 'Unregistered'] as const),
});

export type BuyerInfoFormData = z.infer<typeof buyerInfoSchema>;

/**
 * Zod schema for complete invoice document
 */
export const invoiceDocumentSchema = z.object({
  documentType: z.enum(['SALE_INVOICE', 'DEBIT_NOTE', 'CREDIT_NOTE'] as const),
  referencedInvoiceRefNo: z.string().optional(),
  invoiceType: z.string().min(1, 'Invoice type is required'),
  invoiceDate: z
    .string()
    .min(1, 'Invoice date is required')
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format'),
  invoiceRefNo: z.string().min(1, 'Invoice reference number is required'),
  scenarioId: z.string().default('SN000'),

  // Seller (from stored identity)
  sellerNTNCNIC: z.string().min(1, 'Seller NTN is required'),
  sellerBusinessName: z.string().min(1, 'Seller business name is required'),
  sellerProvince: z.string().min(1, 'Seller province is required'),
  sellerAddress: z.string().min(1, 'Seller address is required'),

  // Buyer
  buyerNTNCNIC: z.string().min(1, 'Buyer NTN/CNIC is required'),
  buyerBusinessName: z.string().min(1, 'Buyer business name is required'),
  buyerProvince: z.string().min(1, 'Buyer province is required'),
  buyerAddress: z.string().min(1, 'Buyer address is required'),
  buyerRegistrationType: z.enum(['Registered', 'Unregistered'] as const),

  // Items
  items: z.array(invoiceItemSchema).min(1, 'At least one item is required'),
}).refine(
  (data) => {
    // Debit and Credit notes must have a referenced invoice
    if (data.documentType === 'DEBIT_NOTE' || data.documentType === 'CREDIT_NOTE') {
      return !!data.referencedInvoiceRefNo && data.referencedInvoiceRefNo.length > 0;
    }
    return true;
  },
  {
    message: 'Referenced invoice is required for Debit/Credit notes',
    path: ['referencedInvoiceRefNo'],
  }
);

export type InvoiceDocumentFormData = z.infer<typeof invoiceDocumentSchema>;

/**
 * Create a new empty invoice item
 */
export function createEmptyItem(): InvoiceItemFormData {
  return {
    id: crypto.randomUUID(),
    hsCode: '',
    productDescription: '',
    rate: '0%',
    uoM: '',
    quantity: 0,
    totalValues: 0,
    valueSalesExcludingST: 0,
    fixedNotifiedValueOrRetailPrice: 0,
    salesTaxApplicable: 0,
    salesTaxWithheldAtSource: 0,
    extraTax: '',
    furtherTax: 0,
    sroScheduleNo: '',
    fedPayable: 0,
    discount: 0,
    saleType: '',
    sroItemSerialNo: '',
  };
}

/**
 * Create default form values for a new invoice
 */
export function createDefaultInvoiceFormData(
  documentType: DocumentType,
  sellerIdentity?: SellerIdentityFormData
): Partial<InvoiceDocumentFormData> {
  const today = new Date().toISOString().split('T')[0];
  const invoiceTypeLabel =
    documentType === 'SALE_INVOICE'
      ? 'Sale Invoice'
      : documentType === 'DEBIT_NOTE'
        ? 'Debit Note'
        : 'Credit Note';

  return {
    documentType,
    invoiceType: invoiceTypeLabel,
    invoiceDate: today,
    invoiceRefNo: '',
    scenarioId: 'SN000',
    sellerNTNCNIC: sellerIdentity?.sellerNTNCNIC ?? '',
    sellerBusinessName: sellerIdentity?.sellerBusinessName ?? '',
    sellerProvince: sellerIdentity?.sellerProvince ?? '',
    sellerAddress: sellerIdentity?.sellerAddress ?? '',
    buyerNTNCNIC: '',
    buyerBusinessName: '',
    buyerProvince: '',
    buyerAddress: '',
    buyerRegistrationType: 'Registered',
    items: [createEmptyItem()],
  };
}
