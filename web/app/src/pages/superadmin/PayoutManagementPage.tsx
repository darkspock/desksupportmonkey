import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
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
    key: 'admin.payouts.status_requested',
    className: 'bg-yellow-100 text-yellow-800',
  },
  approved: {
    key: 'admin.payouts.status_approved',
    className: 'bg-blue-100 text-blue-800',
  },
  paid: {
    key: 'admin.payouts.status_paid',
    className: 'bg-green-100 text-green-800',
  },
  rejected: {
    key: 'admin.payouts.status_rejected',
    className: 'bg-red-100 text-red-800',
  },
};

const PAGE_SIZE = 20;

export default function PayoutManagementPage() {
  const { token } = useAuth();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [actionModal, setActionModal] = useState<{
    payout: Payout;
    action: 'reject' | 'mark_paid';
  } | null>(null);
  const [notes, setNotes] = useState('');
  const [paymentReference, setPaymentReference] = useState('');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin-payouts', offset],
    queryFn: async () => {
      const { data } = await api.get<{ data: PayoutListResponse }>(
        `/admin/payouts/?offset=${offset}&limit=${PAGE_SIZE}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      return data.data;
    },
    enabled: !!token,
  });

  const processMutation = useMutation({
    mutationFn: async ({
      payoutId,
      action,
      payment_reference,
      notes: actionNotes,
    }: {
      payoutId: string;
      action: string;
      payment_reference?: string;
      notes?: string;
    }) => {
      const { data } = await api.patch(
        `/admin/payouts/${payoutId}`,
        { action, payment_reference, notes: actionNotes },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-payouts'] });
      setActionModal(null);
      setNotes('');
      setPaymentReference('');
    },
  });

  const handleApprove = (payout: Payout) => {
    processMutation.mutate({ payoutId: payout.id, action: 'approve' });
  };

  const handleRejectSubmit = () => {
    if (!actionModal) return;
    processMutation.mutate({
      payoutId: actionModal.payout.id,
      action: 'reject',
      notes: notes || undefined,
    });
  };

  const handleMarkPaidSubmit = () => {
    if (!actionModal || !paymentReference.trim()) return;
    processMutation.mutate({
      payoutId: actionModal.payout.id,
      action: 'mark_paid',
      payment_reference: paymentReference.trim(),
    });
  };

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
        <h1 className="text-2xl font-semibold text-foreground">{t('admin.payouts.title')}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t('admin.payouts.subtitle')}</p>
      </div>

      {data.items.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-6 text-center">
          <p className="text-sm text-muted-foreground">{t('admin.payouts.empty')}</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border bg-card">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-secondary/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('admin.payouts.col_reseller')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('admin.payouts.col_amount')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('admin.payouts.col_status')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('admin.payouts.col_requested')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('admin.payouts.col_reference')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('admin.payouts.col_notes')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('admin.payouts.col_actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((p) => {
                  const cfg = statusConfig[p.status] ?? statusConfig.requested;
                  return (
                    <tr key={p.id}>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-foreground">
                        {p.reseller_name}
                      </td>
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
                        {p.payment_reference || '-'}
                      </td>
                      <td className="max-w-[200px] truncate px-4 py-3 text-sm text-muted-foreground">
                        {p.notes || '-'}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <div className="flex items-center gap-1">
                          {p.status === 'requested' && (
                            <>
                              <button
                                type="button"
                                onClick={() => handleApprove(p)}
                                disabled={processMutation.isPending}
                                className="rounded-md bg-green-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
                              >
                                {t('admin.payouts.action_approve')}
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setActionModal({ payout: p, action: 'reject' });
                                  setNotes('');
                                }}
                                disabled={processMutation.isPending}
                                className="rounded-md bg-red-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
                              >
                                {t('admin.payouts.action_reject')}
                              </button>
                            </>
                          )}
                          {p.status === 'approved' && (
                            <button
                              type="button"
                              onClick={() => {
                                setActionModal({ payout: p, action: 'mark_paid' });
                                setPaymentReference('');
                              }}
                              disabled={processMutation.isPending}
                              className="rounded-md bg-blue-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                            >
                              {t('admin.payouts.action_mark_paid')}
                            </button>
                          )}
                        </div>
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

      {/* Reject Modal */}
      {actionModal?.action === 'reject' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('admin.payouts.reject_title')}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {t('admin.payouts.reject_description')} — {formatCents(actionModal.payout.amount_cents)} ({actionModal.payout.reseller_name})
            </p>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={t('admin.payouts.reject_notes_placeholder')}
              className="mt-3 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
              rows={3}
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setActionModal(null)}
                className="rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground hover:bg-secondary"
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                onClick={handleRejectSubmit}
                disabled={processMutation.isPending}
                className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {processMutation.isPending && <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />}
                {t('admin.payouts.action_reject')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mark as Paid Modal */}
      {actionModal?.action === 'mark_paid' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('admin.payouts.mark_paid_title')}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {t('admin.payouts.mark_paid_description')} — {formatCents(actionModal.payout.amount_cents)} ({actionModal.payout.reseller_name})
            </p>
            <input
              type="text"
              value={paymentReference}
              onChange={(e) => setPaymentReference(e.target.value)}
              placeholder={t('admin.payouts.payment_reference_placeholder')}
              className="mt-3 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setActionModal(null)}
                className="rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground hover:bg-secondary"
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                onClick={handleMarkPaidSubmit}
                disabled={processMutation.isPending || !paymentReference.trim()}
                className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {processMutation.isPending && <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />}
                {t('admin.payouts.action_mark_paid')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
