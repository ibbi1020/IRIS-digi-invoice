'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  FileText,
  Home,
  Settings,
  History,
  PlusCircle,
  Menu,
  FileInput,
  FileOutput,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

const navItems = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: Home,
  },
  {
    title: 'New Invoice',
    href: '/invoices/new',
    icon: PlusCircle,
  },
  {
    title: 'New Debit Note',
    href: '/notes/debit/new',
    icon: FileInput,
  },
  {
    title: 'New Credit Note',
    href: '/notes/credit/new',
    icon: FileOutput,
  },
  {
    title: 'History / Attempts',
    href: '/attempts',
    icon: History,
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
  },
];

type SidebarProps = React.HTMLAttributes<HTMLDivElement>;

export function AppSidebar({ className }: SidebarProps) {
  const pathname = usePathname();

  return (
    <div className={cn('pb-12 h-screen overflow-y-auto', className)}> {/* Added h-screen and overflow */}
      <div className="space-y-4 py-4">
        <div className="px-3 py-2">
          <div className="flex items-center px-4 mb-8"> {/* Increased bottom margin for header */}
            <FileText className="mr-2 h-6 w-6 text-foreground" /> {/* Changed primary to foreground for monochrome feel */}
            <h2 className="text-lg font-medium tracking-tight">IRIS Portal</h2>
          </div>
          <div className="space-y-1 flex flex-col gap-0.5"> {/* Added gap-0.5 */}
            {navItems.map((item) => (
              <Button
                key={item.href}
                variant={pathname === item.href ? 'secondary' : 'ghost'}
                className={cn(
                  "w-full justify-start font-normal", /* Reduced weight */
                  pathname === item.href && "font-medium"
                )}
                asChild
              >
                <Link href={item.href}>
                  <item.icon className="mr-3 h-4 w-4 text-muted-foreground" /> {/* Muted icon color */}
                  {item.title}
                </Link>
              </Button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="mr-2 md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle Menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="pr-0">
        <SheetHeader>
          <SheetTitle className="flex items-center">
            <FileText className="mr-2 h-5 w-5 text-foreground" />
            IRIS Portal
          </SheetTitle>
        </SheetHeader>

        <div className="flex flex-col space-y-1 pt-6">
          {navItems.map((item) => (
            <Button
              key={item.href}
              variant={pathname === item.href ? 'secondary' : 'ghost'}
              className={cn(
                "w-full justify-start font-normal",
                pathname === item.href && "font-medium"
              )}
              asChild
              onClick={() => setOpen(false)}
            >
              <Link href={item.href}>
                <item.icon className="mr-3 h-4 w-4 text-muted-foreground" />
                {item.title}
              </Link>
            </Button>
          ))}
        </div>
      </SheetContent>
    </Sheet>
  );
}
