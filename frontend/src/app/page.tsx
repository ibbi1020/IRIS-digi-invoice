import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { FileText, ArrowRight } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex h-14 items-center px-4 lg:px-6 border-b">
        <Link className="flex items-center justify-center" href="#">
          <FileText className="h-6 w-6 text-primary" />
          <span className="ml-2 text-lg font-bold">IRIS Portal</span>
        </Link>
        <nav className="ml-auto flex gap-4 sm:gap-6">
          <Link className="text-sm font-medium hover:underline underline-offset-4" href="/login">
            Login
          </Link>
        </nav>
      </header>
      <main className="flex-1">
        <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48 bg-muted/40">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl/none">
                  Digital Invoicing for Pakistan
                </h1>
                <p className="mx-auto max-w-[700px] text-gray-500 md:text-xl dark:text-gray-400">
                  Seamlessly submit Sales Invoices, Debit Notes, and Credit Notes to FBR Digital Invoicing (IRIS 2.0). 
                  Reliable, fast, and compliant.
                </p>
              </div>
              <div className="space-x-4">
                <Button asChild size="lg">
                    <Link href="/login">
                        Get Started <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                </Button>
                <Button asChild variant="outline" size="lg">
                    <Link href="/dashboard">
                        Go to Dashboard
                    </Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
        <section className="w-full py-12 md:py-24 lg:py-32 bg-background">
          <div className="container px-4 md:px-6">
            <div className="grid gap-10 sm:px-10 md:gap-16 md:grid-cols-2">
              <div className="space-y-4">
                <div className="inline-block rounded-lg bg-muted px-3 py-1 text-sm">
                  Compliance
                </div>
                <h2 className="lg:leading-tighter text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl xl:text-[3.4rem] 2xl:text-[3.75rem]">
                  FBR IRIS 2.0 Ready
                </h2>
                <Button className="w-full sm:w-auto" variant="secondary">View Documentation</Button>
              </div>
              <div className="flex flex-col items-start space-y-4">
                 <ul className="grid gap-6">
                    <li className="flex items-start gap-4">
                        <div className="rounded-full bg-primary/10 p-2 text-primary">
                            <FileText className="h-6 w-6" />
                        </div>
                        <div>
                            <h3 className="font-semibold">Sales Invoices</h3>
                            <p className="text-sm text-gray-500">Create and submit sales invoices in seconds.</p>
                        </div>
                    </li>
                    <li className="flex items-start gap-4">
                        <div className="rounded-full bg-primary/10 p-2 text-primary">
                            <ArrowRight className="h-6 w-6" />
                        </div>
                        <div>
                            <h3 className="font-semibold">Debit & Credit Notes</h3>
                            <p className="text-sm text-gray-500">Handle returns and adjustments easily.</p>
                        </div>
                    </li>
                 </ul>
              </div>
            </div>
          </div>
        </section>
      </main>
      <footer className="flex flex-col gap-2 sm:flex-row py-6 w-full shrink-0 items-center px-4 md:px-6 border-t font-light text-xs text-muted-foreground">
        <p>© 2026 IRIS Portal. Metadata-only logs stored locally.</p>
        <nav className="sm:ml-auto flex gap-4 sm:gap-6">
          <Link className="hover:underline underline-offset-4" href="#">
            Terms of Service
          </Link>
          <Link className="hover:underline underline-offset-4" href="#">
            Privacy
          </Link>
        </nav>
      </footer>
    </div>
  );
}
