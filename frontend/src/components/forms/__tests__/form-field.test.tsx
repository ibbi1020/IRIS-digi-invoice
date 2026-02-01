import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FormField } from '../form-field';
import { z } from 'zod';

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const schema = z.object({
    testField: z.string().min(1, 'Field is required'),
  });

  const methods = useForm({
    resolver: zodResolver(schema),
    defaultValues: { testField: '' },
  });

  return <FormProvider {...methods}>{children}</FormProvider>;
};

describe('FormField', () => {
  it('renders label and input', () => {
    render(
      <TestWrapper>
        <FormField name="testField" label="Test Label" />
      </TestWrapper>
    );

    expect(screen.getByLabelText(/test label/i)).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('shows required indicator when required prop is true', () => {
    render(
      <TestWrapper>
        <FormField name="testField" label="Test Label" required />
      </TestWrapper>
    );

    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('renders placeholder', () => {
    render(
      <TestWrapper>
        <FormField name="testField" label="Test Label" placeholder="Enter value" />
      </TestWrapper>
    );

    expect(screen.getByPlaceholderText('Enter value')).toBeInTheDocument();
  });

  it('disables input when disabled prop is true', () => {
    render(
      <TestWrapper>
        <FormField name="testField" label="Test Label" disabled />
      </TestWrapper>
    );

    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('accepts different input types', () => {
    render(
      <TestWrapper>
        <FormField name="testField" label="Test Label" type="email" />
      </TestWrapper>
    );

    expect(screen.getByRole('textbox')).toHaveAttribute('type', 'email');
  });
});
