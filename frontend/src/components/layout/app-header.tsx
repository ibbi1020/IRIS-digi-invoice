import * as React from 'react';
import Link from 'next/link';
import { MobileNav } from './app-sidebar';
import { User } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function AppHeader() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center pl-4 md:pl-0">
        <MobileNav />
        <div className="mr-4 hidden md:flex">
          {/* Breadcrumbs could go here */}
        </div>
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <nav className="flex items-center space-x-2">
            <Button variant="ghost" size="icon" asChild>
                <Link href="/settings">
                    <User className="h-5 w-5" />
                    <span className="sr-only">User account</span>
                </Link>
            </Button>
          </nav>
        </div>
      </div>
    </header>
  );
}
