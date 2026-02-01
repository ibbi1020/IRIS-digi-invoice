'use client';

import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Save, Building2 } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Alert,
  AlertDescription,
  AlertTitle,
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
import { sellerIdentitySchema, type SellerIdentityFormData } from '@/features/invoicing';
import { getStorageRepository } from '@/lib/storage';

const PROVINCES = [
  'Punjab',
  'Sindh',
  'Khyber Pakhtunkhwa',
  'Balochistan',
  'Islamabad Capital Territory',
  'Gilgit-Baltistan',
  'Azad Jammu & Kashmir',
];

export default function SettingsPage() {
  const [isSaving, setIsSaving] = React.useState(false);
  const [saveSuccess, setSaveSuccess] = React.useState(false);

  const form = useForm<SellerIdentityFormData>({
    resolver: zodResolver(sellerIdentitySchema),
    defaultValues: {
      sellerNTNCNIC: '',
      sellerBusinessName: '',
      sellerProvince: '',
      sellerAddress: '',
    },
  });

  const { reset, formState: { isDirty } } = form;

  // Load existing settings
  React.useEffect(() => {
    async function loadSettings() {
      const repo = getStorageRepository();
      const identity = await repo.getSellerIdentity();
      if (identity) {
        reset(identity);
      }
    }
    loadSettings();
  }, [reset]);

  const onSubmit = async (data: SellerIdentityFormData) => {
    setIsSaving(true);
    setSaveSuccess(false);

    try {
      const repo = getStorageRepository();
      await repo.saveSellerIdentity(data);
      setSaveSuccess(true);
      reset(data); // Reset form state to mark as not dirty
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Configure your seller identity and integration settings
        </p>
      </div>

      {saveSuccess && (
        <Alert variant="success">
          <AlertTitle>Settings saved</AlertTitle>
          <AlertDescription>
            Your seller identity has been saved successfully.
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            <CardTitle>Seller Identity</CardTitle>
          </div>
          <CardDescription>
            This information will be used on all invoices you submit. Make sure it matches
            your FBR registration details.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="sellerNTNCNIC"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>NTN (National Tax Number)</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter your 7-13 digit NTN" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="sellerBusinessName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Business Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter your registered business name" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="sellerProvince"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Province</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a province" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {PROVINCES.map((province) => (
                          <SelectItem key={province} value={province}>
                            {province}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="sellerAddress"
                render={({ field }) => (
                  <FormItem>
                     <FormLabel>Business Address</FormLabel>
                     <FormControl>
                        <Input placeholder="Street, Sector, City" {...field} />
                     </FormControl>
                     <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex justify-end pt-4">
                <Button type="submit" disabled={isSaving || !isDirty}>
                  {isSaving ? (
                    <>
                      <Save className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Save Settings
                    </>
                  )}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Integration Configuration</CardTitle>
          <CardDescription>
            API credentials and endpoint configuration (managed by backend)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground space-y-2">
            <p>
              ⚠️ API tokens and credentials are securely managed by the backend service.
              They are not stored in the browser for security reasons.
            </p>
            <p>
              If you need to update your IRIS/FBR API credentials, please contact your
              system administrator.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
