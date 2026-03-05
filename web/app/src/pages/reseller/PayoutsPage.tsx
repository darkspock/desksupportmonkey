import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useResellerAuth } from '../../contexts/ResellerAuthContext';
import { useI18n } from '../../lib/i18n';
import api from '../../lib/api';
import { cn } from '../../lib/cn';

interface Payout {
  id: string;
  reseller_id: string;
  reseller_name: string;
  amount_cents: number;
  status: string;
  requested_at: string | null;
  processed_at: string | null;
  processed_by: string | null;
  payment_reference: string | null;
  notes: string | null;
}

interface PayoutListResponse {
  items: Payout[];
  total: number;
}

interface DashboardData {
  available_balance_cents: number;
  pending_payout_cents: number;
}

function formatCents(cents: number): string {
  const negative = cents < 0;
  const abs = Math.abs(cents);
  return `${negative ? '-' : ''}$${(abs / 100).toFixed(2)}`;
}

function formatDate(iso: string | null): string {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString();
}

const statusConfig: Record<string, { key: string; className: string }> = {
  requested: {
    key: 'reseller.payouts.status_requested',
    className: 'bg-yellow-100 text-yellow-800',
  },
  approved: {
    key: 'reseller.payouts.status_approved',
    className: 'bg-blue-100 text-blue-800',
  },
  paid: {
    key: 'reseller.payouts.status_paid',
    className: 'bg-green-100 text-green-800',
  },
  rejected: {
    key: 'reseller.payouts.status_rejected',
    className: 'bg-red-100 text-red-800',
  },
};

const PAGE_SIZE = 20;

export default function PayoutsPage() {
  const { token } = useResellerAuth();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);

  const { data: dashboard } = useQuery({
    queryKey: ['reseller-dashboard-payout'],
    queryFn: async () => {
      const { data } = await api.get<{ data: DashboardData }>(
        '/reseller/dashboard',
        { headers: { Authorization: `Bearer ${token}` } },
      );
      return data.data;
    },
    enabled: !!token,
  });

  const { data, isLoading, isError } = useQuery({
    queryKey: ['reseller-payouts', offset],
    queryFn: async () => {
      const { data } = await api.get<{ data: PayoutListResponse }>(
        `/reseller/payouts?offset=${offset}&limit=${PAGE_SIZE}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      return data.data;
    },
    enabled: !!token,
  });

  const requestMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(
        '/reseller/payouts',
        {},
        { headers: { Authorization: `Bearer ${token}` } },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reseller-payouts'] });
      queryClient.invalidateQueries({ queryKey: ['reseller-dashboard-payout'] });
    },
  });

  const availableBalance = dashboard?.available_balance_cents ?? 0;
  const pendingPayout = dashboard?.pending_payout_cents ?? 0;
  const canRequest = availableBalance >= 5000 && pendingPayout === 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-sm text-destructive">
        {t('common.error')}
      </div>
    );
  }

  const totalPages = Math.ceil(data.total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">{t('reseller.payouts.title')}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t('reseller.payouts.subtitle')}</p>
      </div>

      {/* Balance + Request Payout */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-lg border border-border bg-card p-4">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{t('reseller.payouts.balance_label')}</p>
          <p className="text-2xl font-semibold font-mono text-foreground">{formatCents(availableBalance)}</p>
          {pendingPayout > 0 && (
            <p className="text-xs text-muted-foreground">
              {t('reseller.payouts.threshold_label')}: {formatCents(pendingPayout)}
            </p>
          )}
        </div>
        <button
          type="button"
          disabled={!canRequest || requestMutation.isPending}
          onClick={() => requestMutation.mutate()}
          className={cn(
            'inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors',
            canRequest
              ? 'bg-primary text-primary-foreground hover:bg-primary/90'
              : 'bg-secondary text-muted-foreground cursor-not-allowed',
          )}
        >
          {requestMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          {canRequest ? t('reseller.payouts.request_button') : t('reseller.payouts.request_button_disabled')}
        </button>
      </div>

      {requestMutation.isError && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          {(requestMutation.error as Error)?.message || t('common.error')}
        </div>
      )}

      {data.items.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-6 text-center">
          <p className="text-sm text-muted-foreground">{t('reseller.payouts.empty')}</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border bg-card">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-secondary/50">
                <tr>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.payouts.col_amount')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.payouts.col_status')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.payouts.col_requested')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.payouts.col_processed')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.payouts.col_reference')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.payouts.col_notes')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((p) => {
                  const cfg = statusConfig[p.status] ?? statusConfig.requested;
                  return (
                    <tr key={p.id}>
                      <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-mono font-medium text-foreground">
                        {formatCents(p.amount_cents)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <span className={cn('inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase', cfg.className)}>
                          {t(cfg.key)}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                        {formatDate(p.requested_at)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                        {formatDate(p.processed_at)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                        {p.payment_reference || '-'}
                      </td>
                      <td className="max-w-[200px] truncate px-4 py-3 text-sm text-muted-foreground">
                        {p.notes || '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {data.total} {data.total === 1 ? 'payout' : 'payouts'}
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                  className="inline-flex items-center rounded-md border border-border px-2 py-1 text-sm disabled:opacity-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm text-muted-foreground">
                  {currentPage} / {totalPages}
                </span>
                <button
                  type="button"
                  disabled={offset + PAGE_SIZE >= data.total}
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                  className="inline-flex items-center rounded-md border border-border px-2 py-1 text-sm disabled:opacity-50"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
