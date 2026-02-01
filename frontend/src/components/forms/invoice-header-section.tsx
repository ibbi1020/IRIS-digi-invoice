'use client';

import * as React from 'react';
import { useFormContext } from 'react-hook-form';
import { Lightbulb } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, Alert, AlertDescription } from '@/components/ui';
import { FormField } from './form-field';
import type { DocumentType } from '@/types';
import { suggestNextInvoiceRefNo } from '@/features/invoicing';

interface InvoiceHeaderSectionProps {
  documentType: DocumentType;
  disabled?: boolean;
  lastSuccessfulRefNo?: string | null;
  onValidateReference?: (refNo: string) => Promise<{ valid: boolean; reason?: string }>;
}

export function InvoiceHeaderSection({
  documentType,
  disabled,
  lastSuccessfulRefNo,
  onValidateReference,
}: InvoiceHeaderSectionProps) {
  const { setValue, watch, formState: { errors } } = useFormContext();
  const [referenceError, setReferenceError] = React.useState<string | null>(null);
  const [validatingRef, setValidatingRef] = React.useState(false);

  const invoiceRefNo = watch('invoiceRefNo');
  const referencedInvoiceRefNo = watch('referencedInvoiceRefNo');

  const isNoteType = documentType === 'DEBIT_NOTE' || documentType === 'CREDIT_NOTE';
  const suggestedRefNo = suggestNextInvoiceRefNo(lastSuccessfulRefNo ?? null);

  const handleSuggestRefNo = () => {
    if (suggestedRefNo) {
      setValue('invoiceRefNo', suggestedRefNo);
    }
  };

  // Validate referenced invoice for debit/credit notes
  React.useEffect(() => {
    if (!isNoteType || !referencedInvoiceRefNo || !onValidateReference) {
      setReferenceError(null);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setValidatingRef(true);
      try {
        const result = await onValidateReference(referencedInvoiceRefNo);
        setReferenceError(result.valid ? null : result.reason ?? 'Invalid reference');
      } catch {
        setReferenceError('Failed to validate reference');
      } finally {
        setValidatingRef(false);
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [referencedInvoiceRefNo, isNoteType, onValidateReference]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Invoice Details</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            name="invoiceDate"
            label="Invoice Date"
            type="date"
            required
            disabled={disabled}
          />
          <div className="space-y-2">
            <FormField
              name="invoiceRefNo"
              label="Invoice Reference Number"
              required
              placeholder="e.g., INV-0001"
              disabled={disabled}
            />
            {suggestedRefNo && !invoiceRefNo && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleSuggestRefNo}
                disabled={disabled}
                className="text-xs"
              >
                <Lightbulb className="h-3 w-3 mr-1" />
                Suggest: {suggestedRefNo}
              </Button>
            )}
          </div>
        </div>

        {isNoteType && (
          <div className="space-y-2">
            <FormField
              name="referencedInvoiceRefNo"
              label="Referenced Sale Invoice Ref No"
              required
              placeholder="Enter the original sale invoice reference"
              disabled={disabled}
            />
            {validatingRef && (
              <p className="text-sm text-muted-foreground">Validating reference...</p>
            )}
            {referenceError && (
              <Alert variant="destructive">
                <AlertDescription>{referenceError}</AlertDescription>
              </Alert>
            )}
            {referencedInvoiceRefNo && !referenceError && !validatingRef && (
              <p className="text-sm text-green-600">✓ Reference validated</p>
            )}
          </div>
        )}

        <FormField
          name="scenarioId"
          label="Scenario ID"
          placeholder="SN000"
          disabled={disabled}
        />
      </CardContent>
    </Card>
  );
}
