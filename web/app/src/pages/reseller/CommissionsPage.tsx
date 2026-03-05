import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useResellerAuth } from '../../contexts/ResellerAuthContext';
import { useI18n } from '../../lib/i18n';
import api from '../../lib/api';
import { cn } from '../../lib/cn';

interface Commission {
  id: string;
  reseller_id: string;
  company_id: string;
  company_name: string;
  payment_amount_cents: number;
  commission_pct: number;
  commission_amount_cents: number;
  period_start: string | null;
  period_end: string | null;
  status: string;
  created_at: string | null;
}

interface CommissionListResponse {
  items: Commission[];
  total: number;
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
  pending: {
    key: 'reseller.commissions.status_pending',
    className: 'bg-yellow-100 text-yellow-800',
  },
  confirmed: {
    key: 'reseller.commissions.status_confirmed',
    className: 'bg-green-100 text-green-800',
  },
  paid: {
    key: 'reseller.commissions.status_paid',
    className: 'bg-blue-100 text-blue-800',
  },
  clawed_back: {
    key: 'reseller.commissions.status_clawed_back',
    className: 'bg-red-100 text-red-800',
  },
};

const PAGE_SIZE = 20;

export default function CommissionsPage() {
  const { token } = useResellerAuth();
  const { t } = useI18n();
  const [offset, setOffset] = useState(0);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['reseller-commissions', offset],
    queryFn: async () => {
      const { data } = await api.get<{ data: CommissionListResponse }>(
        `/reseller/commissions?offset=${offset}&limit=${PAGE_SIZE}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      return data.data;
    },
    enabled: !!token,
  });

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
        <h1 className="text-2xl font-semibold text-foreground">{t('reseller.commissions.title')}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t('reseller.commissions.subtitle')}</p>
      </div>

      {data.items.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-6 text-center">
          <p className="text-sm text-muted-foreground">{t('reseller.commissions.empty')}</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border bg-card">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-secondary/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.commissions.col_company')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.commissions.col_payment')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.commissions.col_rate')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.commissions.col_earned')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.commissions.col_period')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.commissions.col_status')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.commissions.col_date')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((c) => {
                  const isClawback = c.status === 'clawed_back';
                  const cfg = statusConfig[c.status] ?? statusConfig.pending;

                  return (
                    <tr key={c.id} className={cn(isClawback && 'bg-red-50/50')}>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-foreground">
                        {c.company_name}
                      </td>
                      <td className={cn(
                        'whitespace-nowrap px-4 py-3 text-right text-sm font-mono',
                        isClawback ? 'text-red-600 line-through' : 'text-foreground',
                      )}>
                        {formatCents(c.payment_amount_cents)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-muted-foreground">
                        {c.commission_pct}%
                      </td>
                      <td className={cn(
                        'whitespace-nowrap px-4 py-3 text-right text-sm font-mono font-medium',
                        isClawback ? 'text-red-600 line-through' : 'text-foreground',
                      )}>
                        {formatCents(c.commission_amount_cents)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                        {c.period_start && c.period_end
                          ? `${formatDate(c.period_start)} - ${formatDate(c.period_end)}`
                          : '-'}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <span className={cn('inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase', cfg.className)}>
                          {t(cfg.key)}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                        {formatDate(c.created_at)}
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
                {data.total} {data.total === 1 ? 'commission' : 'commissions'}
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
