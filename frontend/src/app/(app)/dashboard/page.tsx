'use client';

import * as React from 'react';
import Link from 'next/link';
import { PlusCircle, List, MinusCircle, CreditCard, AlertCircle, CheckCircle2, ArrowUpRight } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Button,
  Badge,
} from '@/components/ui';
import { getStorageRepository } from '@/lib/storage';
import type { AttemptEntry, SellerIdentity } from '@/types';

export default function DashboardPage() {
  const [sellerIdentity, setSellerIdentity] = React.useState<SellerIdentity | null>(null);
  const [recentAttempts, setRecentAttempts] = React.useState<AttemptEntry[]>([]);
  const [stats, setStats] = React.useState({
    total: 0,
    success: 0,
    failed: 0,
    unknown: 0,
  });

  React.useEffect(() => {
    async function loadData() {
      const repo = getStorageRepository();
      const identity = await repo.getSellerIdentity();
      setSellerIdentity(identity);

      const attempts = await repo.getAllAttempts(identity?.sellerNTNCNIC);
      setRecentAttempts(attempts.slice(0, 5));

      // Calculate stats
      const total = attempts.length;
      const success = attempts.filter((a) => a.outcome === 'SUCCESS').length;
      const failed = attempts.filter(
        (a) => ['VALIDATION_ERROR', 'AUTH_ERROR', 'DUPLICATE_ERROR'].includes(a.outcome)
      ).length;
      const unknown = attempts.filter(
        (a) => ['TIMEOUT', 'UNKNOWN'].includes(a.outcome)
      ).length;

      setStats({ total, success, failed, unknown });
    }

    loadData();
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Overview of your Digital Invoicing activities
          </p>
        </div>
        {/* Optional: Add a top-level action or date picker here later */}
      </div>

      {!sellerIdentity && (
        <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 shadow-none">
          <CardContent className="flex items-start sm:items-center gap-4 p-6">
            <div className="p-2 bg-amber-100 dark:bg-amber-900/40 rounded-full shrink-0">
              <AlertCircle className="h-5 w-5 text-amber-700 dark:text-amber-400" />
            </div>
            <div className="flex-1 space-y-1">
              <h3 className="font-medium text-amber-900 dark:text-amber-200">Setup Required</h3>
              <p className="text-sm text-amber-800/80 dark:text-amber-300/80">
                Please configure your seller identity settings to start submitting invoices.
              </p>
            </div>
            <Button asChild variant="outline" className="border-amber-200 bg-white hover:bg-amber-50 text-amber-900 hover:text-amber-950">
              <Link href="/settings">Configure Settings</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <section className="space-y-4">
        <h2 className="text-lg font-medium tracking-tight">Quick Actions</h2>
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="group hover:border-primary/50 transition-all duration-200 hover:shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">New Sale Invoice</CardTitle>
              <PlusCircle className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold mb-1">Create</div>
              <p className="text-xs text-muted-foreground mb-4">
                Submit a standard sales invoice
              </p>
              <Button asChild className="w-full" size="sm">
                <Link href="/invoices/new">Get Started</Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="group hover:border-primary/50 transition-all duration-200 hover:shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">New Debit Note</CardTitle>
              <MinusCircle className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold mb-1">Issue</div>
              <p className="text-xs text-muted-foreground mb-4">
                Debit against an existing invoice
              </p>
              <Button asChild variant="secondary" className="w-full" size="sm">
                <Link href="/notes/debit/new">Create Debit Note</Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="group hover:border-primary/50 transition-all duration-200 hover:shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">New Credit Note</CardTitle>
              <CreditCard className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold mb-1">Issue</div>
              <p className="text-xs text-muted-foreground mb-4">
                Credit against an existing invoice
              </p>
              <Button asChild variant="secondary" className="w-full" size="sm">
                <Link href="/notes/credit/new">Create Credit Note</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Statistics */}
      <section className="space-y-4">
        <h2 className="text-lg font-medium tracking-tight">Overview</h2>
        <div className="grid gap-6 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Volume</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <p className="text-xs text-muted-foreground">
                Submissions to date
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Successful</CardTitle>
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.success}</div>
              <p className="text-xs text-muted-foreground">
                Processed without errors
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
              <div className="h-2 w-2 rounded-full bg-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.failed}</div>
              <p className="text-xs text-muted-foreground">
                Validation or auth errors
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending/Other</CardTitle>
              <div className="h-2 w-2 rounded-full bg-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.unknown}</div>
              <p className="text-xs text-muted-foreground">
                Timeouts or unknown states
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Recent Attempts */}
      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between border-b bg-muted/40 px-6 py-4">
          <div className="space-y-0.5">
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest submission attempts to FBR IRIS</CardDescription>
          </div>
          <Button asChild variant="ghost" size="sm" className="gap-1">
            <Link href="/attempts">
              View All <ArrowUpRight className="h-4 w-4" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {recentAttempts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="p-3 bg-muted rounded-full mb-3">
                <List className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium">No activity yet</p>
              <p className="text-sm text-muted-foreground max-w-xs mt-1">
                When you create invoices or notes, they will appear here.
              </p>
            </div>
          ) : (
            <div>
              {recentAttempts.map((attempt) => (
                <div
                  key={attempt.id}
                  className="flex items-center justify-between border-b p-6 last:border-0 hover:bg-muted/40 transition-colors"
                >
                  <div className="space-y-1">
                    <p className="font-medium text-sm flex items-center gap-2">
                      {attempt.invoiceRefNo}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(attempt.timestamp).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right hidden sm:block">
                      <p className="text-xs font-medium">{attempt.documentType.replace('_', ' ')}</p>
                    </div>
                    <Badge
                      variant={
                        attempt.outcome === 'SUCCESS'
                          ? 'success'
                          : attempt.outcome === 'TIMEOUT' || attempt.outcome === 'UNKNOWN'
                            ? 'warning'
                            : 'destructive'
                      }
                    >
                      {attempt.outcome === 'SUCCESS' && <CheckCircle2 className="h-3 w-3 mr-1" />}
                      {attempt.outcome.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
