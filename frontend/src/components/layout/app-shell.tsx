import * as React from 'react';
import { AppSidebar } from './app-sidebar';
import { AppHeader } from './app-header';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex min-h-screen flex-col md:flex-row bg-background">
      {/* Sidebar for desktop */}
      <aside className="hidden border-r bg-muted/30 md:block md:w-64 lg:w-72">
        <AppSidebar className="sticky top-0 h-screen" />
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col">
        <AppHeader />
        <main className="flex-1 space-y-4 p-4 md:p-8 pt-6">
          {children}
        </main>
      </div>
    </div>
  );
}
