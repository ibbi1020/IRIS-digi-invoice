import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { QueryProvider, MSWProvider } from '@/components/providers';
import { Toaster } from '@/components/ui/sonner';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'IRIS Digital Invoicing Portal',
  description: 'Submit Sales Invoices, Debit Notes, and Credit Notes to FBR Digital Invoicing / IRIS 2.0',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <MSWProvider>
          <QueryProvider>
            {children}
            <Toaster />
          </QueryProvider>
        </MSWProvider>
      </body>
    </html>
  );
}
