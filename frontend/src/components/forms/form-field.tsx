'use client';

import * as React from 'react';
import { useFormContext } from 'react-hook-form';
import { Input, Label } from '@/components/ui';
import { cn } from '@/lib/utils';

interface FormFieldProps {
  name: string;
  label: string;
  required?: boolean;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function FormField({
  name,
  label,
  required,
  type = 'text',
  placeholder,
  disabled,
  className,
}: FormFieldProps) {
  const {
    register,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <div className={cn('space-y-2', className)}>
      <Label htmlFor={name} required={required}>
        {label}
      </Label>
      <Input
        id={name}
        type={type}
        placeholder={placeholder}
        disabled={disabled}
        error={!!error}
        {...register(name)}
      />
      {error && (
        <p className="text-sm text-destructive">{error.message as string}</p>
      )}
    </div>
  );
}

interface NumberFieldProps {
  name: string;
  label: string;
  required?: boolean;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  min?: number;
  step?: string;
}

export function NumberField({
  name,
  label,
  required,
  placeholder,
  disabled,
  className,
  min = 0,
  step = '0.01',
}: NumberFieldProps) {
  const {
    register,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <div className={cn('space-y-2', className)}>
      <Label htmlFor={name} required={required}>
        {label}
      </Label>
      <Input
        id={name}
        type="number"
        placeholder={placeholder}
        disabled={disabled}
        error={!!error}
        min={min}
        step={step}
        {...register(name, { valueAsNumber: true })}
      />
      {error && (
        <p className="text-sm text-destructive">{error.message as string}</p>
      )}
    </div>
  );
}

interface SelectFieldProps {
  name: string;
  label: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  options: { value: string; label: string }[];
}

export function SelectField({
  name,
  label,
  required,
  disabled,
  className,
  options,
}: SelectFieldProps) {
  const {
    register,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <div className={cn('space-y-2', className)}>
      <Label htmlFor={name} required={required}>
        {label}
      </Label>
      <select
        id={name}
        disabled={disabled}
        className={cn(
          'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          error && 'border-destructive focus-visible:ring-destructive'
        )}
        {...register(name)}
      >
        <option value="">Select...</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && (
        <p className="text-sm text-destructive">{error.message as string}</p>
      )}
    </div>
  );
}
