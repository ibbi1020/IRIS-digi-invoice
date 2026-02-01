import type { AttemptOutcome } from './invoice';

/**
 * API error categories per PRD section 8
 */
export type ApiErrorCategory =
  | 'VALIDATION'
  | 'AUTH'
  | 'DUPLICATE'
  | 'TRANSIENT'
  | 'UNKNOWN';

/**
 * Field-level validation error
 */
export interface FieldError {
  field: string;
  message: string;
  code?: string;
}

/**
 * Structured API error response
 */
export interface ApiError {
  category: ApiErrorCategory;
  message: string;
  diagnosticId: string;
  httpStatus?: number;
  fieldErrors?: FieldError[];
  rawResponse?: string;
  retryable: boolean;
}

/**
 * Successful submit response from BFF
 */
export interface SubmitSuccessResponse {
  success: true;
  invoiceRefNo: string;
  message?: string;
  irisReference?: string;
  timestamp: string;
}

/**
 * Error submit response from BFF
 */
export interface SubmitErrorResponse {
  success: false;
  error: ApiError;
}

/**
 * Combined submit response type
 */
export type SubmitResponse = SubmitSuccessResponse | SubmitErrorResponse;

/**
 * Request payload for submitting an invoice to BFF
 * Matches JSON format described in PRD section 7.3
 */
export interface SubmitInvoiceRequest {
  invoiceType: string;
  invoiceDate: string;
  sellerNTNCNIC: string;
  sellerBusinessName: string;
  sellerProvince: string;
  sellerAddress: string;
  buyerNTNCNIC: string;
  buyerBusinessName: string;
  buyerProvince: string;
  buyerAddress: string;
  buyerRegistrationType: string;
  invoiceRefNo: string;
  scenarioId: string;
  items: SubmitInvoiceItem[];
}

/**
 * Line item in submit request
 */
export interface SubmitInvoiceItem {
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
  saleType: string;
  sroItemSerialNo: string;
}

/**
 * Maps AttemptOutcome to ApiErrorCategory
 */
export function outcomeToErrorCategory(outcome: AttemptOutcome): ApiErrorCategory | null {
  switch (outcome) {
    case 'SUCCESS':
      return null;
    case 'VALIDATION_ERROR':
      return 'VALIDATION';
    case 'AUTH_ERROR':
      return 'AUTH';
    case 'DUPLICATE_ERROR':
      return 'DUPLICATE';
    case 'TIMEOUT':
      return 'TRANSIENT';
    case 'UNKNOWN':
      return 'UNKNOWN';
    default:
      return 'UNKNOWN';
  }
}
