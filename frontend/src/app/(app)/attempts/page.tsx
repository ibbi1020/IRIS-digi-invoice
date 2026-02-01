'use client';

import * as React from 'react';
import { Download, FileText, Search, Filter } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
} from '@/components/ui';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { getStorageRepository } from '@/lib/storage';
import {
  generateAttemptsCsv,
  downloadFile,
  formatTimestamp,
  getDocumentTypeLabel,
} from '@/features/invoicing/utils';
import type { AttemptEntry, AttemptOutcome } from '@/types';

const OUTCOME_BADGES: Record<
  AttemptOutcome,
  { variant: 'success' | 'destructive' | 'warning' | 'secondary'; label: string }
> = {
  SUCCESS: { variant: 'success', label: 'Success' },
  VALIDATION_ERROR: { variant: 'destructive', label: 'Validation Error' },
  AUTH_ERROR: { variant: 'destructive', label: 'Auth Error' },
  DUPLICATE_ERROR: { variant: 'destructive', label: 'Duplicate' },
  TIMEOUT: { variant: 'warning', label: 'Timeout' },
  UNKNOWN: { variant: 'warning', label: 'Unknown' },
};

export default function AttemptsPage() {
  const [attempts, setAttempts] = React.useState<AttemptEntry[]>([]);
  const [filteredAttempts, setFilteredAttempts] = React.useState<AttemptEntry[]>([]);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedOutcome, setSelectedOutcome] = React.useState<AttemptOutcome | 'ALL'>('ALL');
  const [selectedAttempt, setSelectedAttempt] = React.useState<AttemptEntry | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    async function loadAttempts() {
      const repo = getStorageRepository();
      const allAttempts = await repo.getAllAttempts();
      setAttempts(allAttempts);
      setFilteredAttempts(allAttempts);
      setIsLoading(false);
    }
    loadAttempts();
  }, []);

  // Filter attempts
  React.useEffect(() => {
    let result = attempts;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          a.invoiceRefNo.toLowerCase().includes(query) ||
          a.diagnosticId.toLowerCase().includes(query) ||
          a.sellerNTNCNIC.includes(query)
      );
    }

    if (selectedOutcome !== 'ALL') {
      result = result.filter((a) => a.outcome === selectedOutcome);
    }

    setFilteredAttempts(result);
  }, [attempts, searchQuery, selectedOutcome]);

  const handleExportCsv = () => {
    const csv = generateAttemptsCsv(filteredAttempts);
    const filename = `iris-attempts-${new Date().toISOString().split('T')[0]}.csv`;
    downloadFile(csv, filename, 'text/csv');
  };

  const handleExportPdf = () => {
    // TODO: Implement PDF export using a library like jsPDF or react-pdf
    // For MVP, show a placeholder message
    alert(
      'PDF export is coming soon. For now, please use CSV export.\n\n' +
        'Recommended library: jsPDF or @react-pdf/renderer'
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Attempt Ledger</h1>
          <p className="text-muted-foreground">
            View all invoice submission attempts and their outcomes
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExportPdf}>
            <FileText className="h-4 w-4 mr-2" />
            PDF Summary
          </Button>
          <Button onClick={handleExportCsv}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by invoice ref, diagnostic ID, or NTN..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <select
                value={selectedOutcome}
                onChange={(e) => setSelectedOutcome(e.target.value as AttemptOutcome | 'ALL')}
                className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="ALL">All Outcomes</option>
                <option value="SUCCESS">Success</option>
                <option value="VALIDATION_ERROR">Validation Error</option>
                <option value="AUTH_ERROR">Auth Error</option>
                <option value="DUPLICATE_ERROR">Duplicate</option>
                <option value="TIMEOUT">Timeout</option>
                <option value="UNKNOWN">Unknown</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Attempts table */}
      <Card>
        <CardHeader>
          <CardTitle>Submission Attempts</CardTitle>
          <CardDescription>
            Showing {filteredAttempts.length} of {attempts.length} attempts
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : filteredAttempts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {attempts.length === 0
                ? 'No submission attempts yet. Submit an invoice to see attempts here.'
                : 'No attempts match your search criteria.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Invoice Ref</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Attempt #</TableHead>
                    <TableHead>Outcome</TableHead>
                    <TableHead className="text-right">Duration</TableHead>
                    <TableHead>Diagnostic ID</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAttempts.map((attempt) => {
                    const badge = OUTCOME_BADGES[attempt.outcome];
                    return (
                      <TableRow
                        key={attempt.id}
                        className="cursor-pointer"
                        onClick={() => setSelectedAttempt(attempt)}
                      >
                        <TableCell>{formatTimestamp(attempt.timestamp)}</TableCell>
                        <TableCell className="font-medium">{attempt.invoiceRefNo}</TableCell>
                        <TableCell>{getDocumentTypeLabel(attempt.documentType)}</TableCell>
                        <TableCell>{attempt.attemptNumber}</TableCell>
                        <TableCell>
                          <Badge variant={badge.variant}>{badge.label}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {attempt.durationMs ? `${attempt.durationMs}ms` : '-'}
                        </TableCell>
                        <TableCell className="font-mono text-xs">{attempt.diagnosticId}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Modal */}
      <Dialog open={!!selectedAttempt} onOpenChange={(open) => !open && setSelectedAttempt(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
                <DialogTitle>Attempt Details</DialogTitle>
                <DialogDescription>
                    Detailed log for attempt execution.
                </DialogDescription>
            </DialogHeader>
            {selectedAttempt && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Invoice Ref:</span>
                  <p className="font-medium">{selectedAttempt.invoiceRefNo}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Document Type:</span>
                  <p className="font-medium">
                    {getDocumentTypeLabel(selectedAttempt.documentType)}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Timestamp:</span>
                  <p className="font-medium">{formatTimestamp(selectedAttempt.timestamp)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Attempt Number:</span>
                  <p className="font-medium">{selectedAttempt.attemptNumber}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Outcome:</span>
                  <p>
                    <Badge variant={OUTCOME_BADGES[selectedAttempt.outcome].variant}>
                      {OUTCOME_BADGES[selectedAttempt.outcome].label}
                    </Badge>
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">HTTP Status:</span>
                  <p className="font-medium">{selectedAttempt.httpStatus ?? 'N/A'}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Duration:</span>
                  <p className="font-medium">
                    {selectedAttempt.durationMs ? `${selectedAttempt.durationMs}ms` : 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Seller NTN:</span>
                  <p className="font-medium">{selectedAttempt.sellerNTNCNIC}</p>
                </div>
              </div>

              <div>
                <span className="text-muted-foreground text-sm">Diagnostic ID:</span>
                <p className="font-mono text-sm bg-muted p-2 rounded mt-1">
                  {selectedAttempt.diagnosticId}
                </p>
              </div>

              <div>
                <span className="text-muted-foreground text-sm">Endpoint:</span>
                <p className="font-mono text-sm bg-muted p-2 rounded mt-1">
                  {selectedAttempt.endpoint}
                </p>
              </div>

              {selectedAttempt.responseSummary && (
                <div>
                  <span className="text-muted-foreground text-sm">Response Summary:</span>
                  <p className="text-sm bg-muted p-2 rounded mt-1 whitespace-pre-wrap">
                    {selectedAttempt.responseSummary}
                  </p>
                </div>
              )}

              {selectedAttempt.errorDetails && (
                <div>
                  <span className="text-muted-foreground text-sm">Error Details:</span>
                  <p className="text-sm bg-destructive/10 text-destructive p-2 rounded mt-1 whitespace-pre-wrap">
                    {selectedAttempt.errorDetails}
                  </p>
                </div>
              )}
            </div>
            )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
