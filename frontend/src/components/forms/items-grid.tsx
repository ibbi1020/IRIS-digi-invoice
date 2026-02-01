'use client';

import * as React from 'react';
import { useFieldArray, useFormContext } from 'react-hook-form';
import { Plus, Trash2 } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button, Input, Label } from '@/components/ui';
import { createEmptyItem } from '@/features/invoicing';
import { cn } from '@/lib/utils';

interface ItemsGridProps {
  disabled?: boolean;
}

export function ItemsGrid({ disabled }: ItemsGridProps) {
  const {
    control,
    register,
    formState: { errors },
  } = useFormContext();

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'items',
  });

  const itemErrors = errors.items as { message?: string } | undefined;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label className="text-base font-semibold">Line Items</Label>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => append(createEmptyItem())}
          disabled={disabled}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Item
        </Button>
      </div>

      {itemErrors?.message && (
        <p className="text-sm text-destructive">{itemErrors.message}</p>
      )}

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-left w-[120px]">HS Code</TableHead>
              <TableHead className="text-left min-w-[200px]">Description</TableHead>
              <TableHead className="text-left w-[100px]">Rate</TableHead>
              <TableHead className="text-left w-[100px]">UoM</TableHead>
              <TableHead className="text-right w-[100px]">Qty</TableHead>
              <TableHead className="text-right w-[140px]">Value (excl. ST)</TableHead>
              <TableHead className="text-right w-[120px]">Sales Tax</TableHead>
              <TableHead className="text-right w-[140px]">Total</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {fields.map((field, index) => {
              const fieldErrors = (errors.items as Record<number, Record<string, { message?: string }>> | undefined)?.[index];
              
              return (
                <TableRow key={field.id}>
                  <TableCell>
                    <Input
                      {...register(`items.${index}.hsCode`)}
                      placeholder="0000.0000"
                      disabled={disabled}
                      error={!!fieldErrors?.hsCode}
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      {...register(`items.${index}.productDescription`)}
                      placeholder="Product name"
                      disabled={disabled}
                      error={!!fieldErrors?.productDescription}
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      {...register(`items.${index}.rate`)}
                      placeholder="0%"
                      disabled={disabled}
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      {...register(`items.${index}.uoM`)}
                      placeholder="PCS"
                      disabled={disabled}
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      {...register(`items.${index}.quantity`, { valueAsNumber: true })}
                      placeholder="0"
                      disabled={disabled}
                      className="text-right"
                      min={0}
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      {...register(`items.${index}.valueSalesExcludingST`, { valueAsNumber: true })}
                      placeholder="0.00"
                      disabled={disabled}
                      className="text-right"
                      min={0}
                      step="0.01"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      {...register(`items.${index}.salesTaxApplicable`, { valueAsNumber: true })}
                      placeholder="0.00"
                      disabled={disabled}
                      className="text-right"
                      min={0}
                      step="0.01"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      {...register(`items.${index}.totalValues`, { valueAsNumber: true })}
                      placeholder="0.00"
                      disabled={disabled}
                      className="text-right"
                      min={0}
                      step="0.01"
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => remove(index)}
                      disabled={disabled || fields.length === 1}
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {fields.length === 0 && (
        <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
          No items added. Click &quot;Add Item&quot; to add a line item.
        </div>
      )}
    </div>
  );
}
