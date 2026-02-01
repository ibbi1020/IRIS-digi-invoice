'use client';

import * as React from 'react';
import { useFormContext } from 'react-hook-form';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { FormField } from './form-field';

interface BuyerInfoSectionProps {
  disabled?: boolean;
}

const PROVINCES = [
  { value: 'Punjab', label: 'Punjab' },
  { value: 'Sindh', label: 'Sindh' },
  { value: 'Khyber Pakhtunkhwa', label: 'Khyber Pakhtunkhwa' },
  { value: 'Balochistan', label: 'Balochistan' },
  { value: 'Islamabad Capital Territory', label: 'Islamabad Capital Territory' },
  { value: 'Gilgit-Baltistan', label: 'Gilgit-Baltistan' },
  { value: 'Azad Jammu & Kashmir', label: 'Azad Jammu & Kashmir' },
];

const REGISTRATION_TYPES = [
  { value: 'Registered', label: 'Registered' },
  { value: 'Unregistered', label: 'Unregistered' },
];

export function BuyerInfoSection({ disabled }: BuyerInfoSectionProps) {
  const { register, formState: { errors } } = useFormContext();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Buyer Information</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FormField
          name="buyerNTNCNIC"
          label="NTN/CNIC"
          required
          placeholder="Enter buyer NTN or CNIC"
          disabled={disabled}
        />
        <FormField
          name="buyerBusinessName"
          label="Business Name"
          required
          placeholder="Enter buyer business name"
          disabled={disabled}
        />
        <div className="space-y-2">
          <label htmlFor="buyerProvince" className="text-sm font-medium">
            Province <span className="text-destructive">*</span>
          </label>
          <select
            id="buyerProvince"
            disabled={disabled}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            {...register('buyerProvince')}
          >
            <option value="">Select province...</option>
            {PROVINCES.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
          {errors.buyerProvince && (
            <p className="text-sm text-destructive">{errors.buyerProvince.message as string}</p>
          )}
        </div>
        <div className="space-y-2">
          <label htmlFor="buyerRegistrationType" className="text-sm font-medium">
            Registration Type <span className="text-destructive">*</span>
          </label>
          <select
            id="buyerRegistrationType"
            disabled={disabled}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            {...register('buyerRegistrationType')}
          >
            {REGISTRATION_TYPES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </div>
        <div className="md:col-span-2">
          <FormField
            name="buyerAddress"
            label="Address"
            required
            placeholder="Enter buyer address"
            disabled={disabled}
          />
        </div>
      </CardContent>
    </Card>
  );
}
