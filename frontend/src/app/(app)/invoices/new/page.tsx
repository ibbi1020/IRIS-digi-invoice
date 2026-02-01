'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Send, AlertTriangle, CheckCircle2 } from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui';
import {
  InvoiceHeaderSection,
  BuyerInfoSection,
  ItemsGrid,
} from '@/components/forms';
import {
  invoiceDocumentSchema,
  createDefaultInvoiceFormData,
  type InvoiceDocumentFormData,
} from '@/features/invoicing';
import { mapDocumentToRequest } from '@/features/invoicing/utils';
import { getStorageRepository } from '@/lib/storage';
import { submitInvoice, errorToOutcome, type SubmitAttemptResult } from '@/lib/api';
import type { InvoiceDocument, AttemptEntry, SellerIdentity } from '@/types';

export default function NewInvoicePage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = React.useState(false);
  const [blockReason, setBlockReason] = React.useState<string | null>(null);
  const [sellerIdentity, setSellerIdentity] = React.useState<SellerIdentity | null>(null);
  const [lastSuccessfulRef, setLastSuccessfulRef] = React.useState<string | null>(null);

  const methods = useForm<InvoiceDocumentFormData>({
    resolver: zodResolver(invoiceDocumentSchema),
    defaultValues: createDefaultInvoiceFormData('SALE_INVOICE'),
  });

  const { handleSubmit, watch, setError } = methods;
  const invoiceRefNo = watch('invoiceRefNo');

  // Load seller identity and last successful ref
  React.useEffect(() => {
    async function loadData() {
      const repo = getStorageRepository();
      const identity = await repo.getSellerIdentity();
      setSellerIdentity(identity);

      if (identity) {
        methods.setValue('sellerNTNCNIC', identity.sellerNTNCNIC);
        methods.setValue('sellerBusinessName', identity.sellerBusinessName);
        methods.setValue('sellerProvince', identity.sellerProvince);
        methods.setValue('sellerAddress', identity.sellerAddress);

        const lastRef = await repo.getLastSuccessfulRefNo(identity.sellerNTNCNIC);
        setLastSuccessfulRef(lastRef);
      }
    }
    loadData();
  }, [methods]);

  // Check for duplicate/blocked invoiceRefNo
  React.useEffect(() => {
    if (!invoiceRefNo || !sellerIdentity) {
      setBlockReason(null);
      return;
    }

    const checkDuplicate = async () => {
      const repo = getStorageRepository();
      const { used, status } = await repo.isInvoiceRefNoUsed(
        invoiceRefNo,
        sellerIdentity.sellerNTNCNIC
      );

      if (used) {
        if (status === 'SUCCESS') {
          setBlockReason(
            `Invoice reference "${invoiceRefNo}" has already been successfully submitted. Please use a different reference number.`
          );
        } else if (status === 'UNKNOWN') {
          setBlockReason(
            `Invoice reference "${invoiceRefNo}" has an unknown submission status. Please use a different reference number or wait for reconciliation.`
          );
        } else {
          setBlockReason(null);
        }
      } else {
        setBlockReason(null);
      }
    };

    const timeoutId = setTimeout(checkDuplicate, 300);
    return () => clearTimeout(timeoutId);
  }, [invoiceRefNo, sellerIdentity]);

  const onSubmit = async (data: InvoiceDocumentFormData) => {
    if (!sellerIdentity) {
      setSubmitError('Please configure your seller identity in Settings first.');
      return;
    }

    if (blockReason) {
      return; // Blocked by duplicate check
    }

    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);

    const repo = getStorageRepository();

    // Create document
    const documentId = crypto.randomUUID();
    const now = new Date().toISOString();

    const document: InvoiceDocument = {
      id: documentId,
      createdAt: now,
      updatedAt: now,
      documentType: 'SALE_INVOICE',
      invoiceType: data.invoiceType,
      invoiceDate: data.invoiceDate,
      invoiceRefNo: data.invoiceRefNo,
      scenarioId: data.scenarioId,
      sellerNTNCNIC: data.sellerNTNCNIC,
      sellerBusinessName: data.sellerBusinessName,
      sellerProvince: data.sellerProvince,
      sellerAddress: data.sellerAddress,
      buyerNTNCNIC: data.buyerNTNCNIC,
      buyerBusinessName: data.buyerBusinessName,
      buyerProvince: data.buyerProvince,
      buyerAddress: data.buyerAddress,
      buyerRegistrationType: data.buyerRegistrationType,
      items: data.items,
    };

    // Save document
    await repo.saveDocument(document);

    // Prepare request
    const request = mapDocumentToRequest(document);

    // Track attempts
    let attemptNumber = 1;

    const handleAttemptComplete = async (result: SubmitAttemptResult) => {
      const attempt: AttemptEntry = {
        id: crypto.randomUUID(),
        documentId,
        invoiceRefNo: data.invoiceRefNo,
        sellerNTNCNIC: data.sellerNTNCNIC,
        documentType: 'SALE_INVOICE',
        attemptNumber: result.attemptNumber,
        timestamp: new Date().toISOString(),
        endpoint: '/api/bff/invoices/submit',
        outcome: result.success ? 'SUCCESS' : errorToOutcome(result.error!),
        diagnosticId: result.diagnosticId,
        httpStatus: result.error?.httpStatus,
        responseSummary: result.success
          ? 'Invoice submitted successfully'
          : result.error?.message,
        durationMs: result.durationMs,
      };

      await repo.saveAttempt(attempt);
      attemptNumber++;
    };

    try {
      const result = await submitInvoice(request, handleAttemptComplete);

      if (result.success) {
        setSubmitSuccess(true);
        // Redirect to dashboard after short delay
        setTimeout(() => {
          router.push('/dashboard');
        }, 2000);
      } else {
        const error = result.error!;

        // Handle field-level errors
        if (error.fieldErrors) {
          error.fieldErrors.forEach((fe) => {
            setError(fe.field as keyof InvoiceDocumentFormData, {
              type: 'server',
              message: fe.message,
            });
          });
        }

        setSubmitError(
          `${error.message}${error.diagnosticId ? ` (Diagnostic ID: ${error.diagnosticId})` : ''}`
        );
      }
    } catch (err) {
      setSubmitError('An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!sellerIdentity) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">New Sale Invoice</h1>
          <p className="text-muted-foreground">
            Create and submit a new sales invoice to FBR
          </p>
        </div>

        <Alert variant="warning">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Setup Required</AlertTitle>
          <AlertDescription>
            Please configure your seller identity in Settings before creating invoices.
          </AlertDescription>
        </Alert>

        <Button onClick={() => router.push('/settings')}>Go to Settings</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">New Sale Invoice</h1>
        <p className="text-muted-foreground">
          Create and submit a new sales invoice to FBR
        </p>
      </div>

      {submitSuccess && (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          <AlertTitle>Invoice Submitted Successfully</AlertTitle>
          <AlertDescription>
            Your invoice has been submitted to FBR. Redirecting to dashboard...
          </AlertDescription>
        </Alert>
      )}

      {submitError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Submission Failed</AlertTitle>
          <AlertDescription>{submitError}</AlertDescription>
        </Alert>
      )}

      {blockReason && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Cannot Submit</AlertTitle>
          <AlertDescription>{blockReason}</AlertDescription>
        </Alert>
      )}

      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <InvoiceHeaderSection
            documentType="SALE_INVOICE"
            disabled={isSubmitting || submitSuccess}
            lastSuccessfulRefNo={lastSuccessfulRef}
          />

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Seller Information</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">NTN:</span>{' '}
                <span className="font-medium">{sellerIdentity.sellerNTNCNIC}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Business:</span>{' '}
                <span className="font-medium">{sellerIdentity.sellerBusinessName}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Province:</span>{' '}
                <span className="font-medium">{sellerIdentity.sellerProvince}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Address:</span>{' '}
                <span className="font-medium">{sellerIdentity.sellerAddress}</span>
              </div>
            </CardContent>
          </Card>

          <BuyerInfoSection disabled={isSubmitting || submitSuccess} />

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Line Items</CardTitle>
            </CardHeader>
            <CardContent>
              <ItemsGrid disabled={isSubmitting || submitSuccess} />
            </CardContent>
          </Card>

          <div className="flex justify-end gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push('/dashboard')}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              loading={isSubmitting}
              disabled={!!blockReason || submitSuccess}
            >
              <Send className="h-4 w-4 mr-2" />
              Submit Invoice
            </Button>
          </div>
        </form>
      </FormProvider>
    </div>
  );
}
