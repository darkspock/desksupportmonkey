import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Plus, Edit, Eye, X, Check, XCircle } from 'lucide-react';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';
import api from '../../lib/api';
import type { Reseller, ResellerStatus } from '../../types';
import { Tooltip } from '../../components/ui/Tooltip';

interface ResellerListResponse {
  items: Reseller[];
  total: number;
}

function StatusBadge({ status }: { status: ResellerStatus }) {
  const colors: Record<ResellerStatus, string> = {
    pending: 'bg-amber-50 text-amber-700',
    active: 'bg-green-50 text-green-700',
    suspended: 'bg-yellow-50 text-yellow-700',
    deactivated: 'bg-red-50 text-red-700',
  };
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize ${colors[status]}`}>
      {status}
    </span>
  );
}

export default function ResellersPage() {
  const { t } = useI18n();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [filterTab, setFilterTab] = useState<'all' | 'pending'>('all');

  const [createOpen, setCreateOpen] = useState(false);
  const [editReseller, setEditReseller] = useState<Reseller | null>(null);
  const [detailReseller, setDetailReseller] = useState<Reseller | null>(null);
  const [rejectModalReseller, setRejectModalReseller] = useState<Reseller | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  // Form state — create
  const [createEmail, setCreateEmail] = useState('');
  const [createName, setCreateName] = useState('');
  const [createCommission, setCreateCommission] = useState('20');
  const [createMinPayout, setCreateMinPayout] = useState('50');

  // Form state — edit
  const [editName, setEditName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editCompanyName, setEditCompanyName] = useState('');
  const [editTaxId, setEditTaxId] = useState('');
  const [editReferralCode, setEditReferralCode] = useState('');
  const [editCommission, setEditCommission] = useState('');
  const [editMinPayout, setEditMinPayout] = useState('');
  const [editStatus, setEditStatus] = useState('');

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-resellers', page],
    queryFn: async () => {
      const offset = (page - 1) * pageSize;
      const { data } = await api.get<{ data: ResellerListResponse }>(`/admin/resellers/?offset=${offset}&limit=${pageSize}`);
      return data.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (payload: { email: string; name: string; commission_pct: number; min_payout_cents: number }) => {
      await api.post('/admin/resellers/', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-resellers'] });
      setCreateOpen(false);
      resetCreateForm();
      showToast({ title: t('reseller.admin.created') });
    },
    onError: (error: unknown) => {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast({ title: t('common.error'), description: detail ?? t('reseller.admin.create_error'), variant: 'error' });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Record<string, unknown> }) => {
      await api.patch(`/admin/resellers/${id}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-resellers'] });
      setEditReseller(null);
      showToast({ title: t('reseller.admin.updated') });
    },
    onError: (error: unknown) => {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast({ title: t('common.error'), description: detail ?? t('reseller.admin.update_error'), variant: 'error' });
    },
  });

  const approveMutation = useMutation({
    mutationFn: async (resellerId: string) => {
      await api.post(`/admin/resellers/${resellerId}/approve`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-resellers'] });
      showToast({ title: t('reseller.admin.approved_success') });
    },
    onError: (error: unknown) => {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast({ title: t('common.error'), description: detail ?? t('common.error'), variant: 'error' });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string | null }) => {
      await api.post(`/admin/resellers/${id}/reject`, { reason: reason || null });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-resellers'] });
      setRejectModalReseller(null);
      setRejectReason('');
      showToast({ title: t('reseller.admin.rejected_success') });
    },
    onError: (error: unknown) => {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast({ title: t('common.error'), description: detail ?? t('common.error'), variant: 'error' });
    },
  });

  const filteredItems = data?.items.filter((r) => {
    if (filterTab === 'pending') return r.status === 'pending';
    return true;
  }) ?? [];

  const pendingCount = data?.items.filter((r) => r.status === 'pending').length ?? 0;

  const resetCreateForm = () => {
    setCreateEmail('');
    setCreateName('');
    setCreateCommission('20');
    setCreateMinPayout('50');
  };

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      email: createEmail,
      name: createName,
      commission_pct: parseInt(createCommission, 10),
      min_payout_cents: parseInt(createMinPayout, 10) * 100,
    });
  };

  const handleEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editReseller) return;
    const payload: Record<string, unknown> = {};
    if (editName && editName !== editReseller.name) payload.name = editName;
    if (editEmail && editEmail !== editReseller.email) payload.email = editEmail;
    if (editCompanyName !== (editReseller.company_name ?? '')) payload.company_name = editCompanyName || null;
    if (editTaxId !== (editReseller.tax_id ?? '')) payload.tax_id = editTaxId || null;
    if (editReferralCode && editReferralCode !== editReseller.referral_code) payload.referral_code = editReferralCode;
    if (editCommission) payload.commission_pct = parseInt(editCommission, 10);
    if (editMinPayout) payload.min_payout_cents = parseInt(editMinPayout, 10) * 100;
    if (editStatus) payload.status = editStatus;
    updateMutation.mutate({ id: editReseller.id, payload });
  };

  const openEdit = (r: Reseller) => {
    setEditReseller(r);
    setEditName(r.name);
    setEditEmail(r.email);
    setEditCompanyName(r.company_name ?? '');
    setEditTaxId(r.tax_id ?? '');
    setEditReferralCode(r.referral_code);
    setEditCommission(String(r.commission_pct));
    setEditMinPayout(String(r.min_payout_cents / 100));
    setEditStatus(r.status);
  };

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-sm text-destructive">{t('common.error')}</div>
        <button onClick={() => refetch()} className="text-sm text-primary hover:underline">{t('common.retry')}</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">{t('reseller.admin.title')}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t('reseller.admin.subtitle')}</p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          {t('reseller.admin.add_reseller')}
        </button>
      </div>

      {/* Tab filter */}
      <div className="flex gap-1 rounded-lg border border-border bg-secondary/30 p-1 w-fit">
        <button
          onClick={() => { setFilterTab('all'); setPage(1); }}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${filterTab === 'all' ? 'bg-card text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'}`}
        >
          {t('reseller.admin.all_tab')}
        </button>
        <button
          onClick={() => { setFilterTab('pending'); setPage(1); }}
          className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition ${filterTab === 'pending' ? 'bg-card text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'}`}
        >
          {t('reseller.admin.pending_tab')}
          {pendingCount > 0 && (
            <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-amber-100 px-1.5 text-xs font-semibold text-amber-700">
              {pendingCount}
            </span>
          )}
        </button>
      </div>

      {data && data.items.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <p className="text-sm text-muted-foreground">{t('reseller.admin.empty')}</p>
          <button
            onClick={() => setCreateOpen(true)}
            className="mt-3 text-sm font-medium text-primary hover:underline"
          >
            {t('reseller.admin.add_first')}
          </button>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border bg-card">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/50">
                  <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">{t('reseller.admin.col_name')}</th>
                  <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">{t('reseller.admin.col_email')}</th>
                  <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">{t('reseller.admin.col_commission')}</th>
                  <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">{t('reseller.admin.col_min_payout')}</th>
                  <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">{t('reseller.admin.col_referral')}</th>
                  <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">{t('common.status')}</th>
                  <th className="px-4 py-2.5 text-right font-medium text-muted-foreground">{t('reseller.admin.col_actions')}</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((r) => (
                  <tr key={r.id} className="border-b border-border last:border-0 hover:bg-secondary/30">
                    <td className="px-4 py-2.5 font-medium text-foreground">{r.name}</td>
                    <td className="px-4 py-2.5 text-muted-foreground">{r.email}</td>
                    <td className="px-4 py-2.5 text-foreground">{r.commission_pct}%</td>
                    <td className="px-4 py-2.5 text-foreground">${(r.min_payout_cents / 100).toFixed(2)}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-foreground">{r.referral_code}</td>
                    <td className="px-4 py-2.5"><StatusBadge status={r.status} /></td>
                    <td className="px-4 py-2.5 text-right">
                      {r.status === 'pending' ? (
                        <div className="flex items-center justify-end gap-1">
                          <Tooltip content={t('reseller.admin.approve')}>
                            <button
                              onClick={() => approveMutation.mutate(r.id)}
                              disabled={approveMutation.isPending}
                              className="rounded p-1 text-green-600 hover:bg-green-50 hover:text-green-700"
                              aria-label={t('reseller.admin.approve')}
                            >
                              <Check className="h-4 w-4" />
                            </button>
                          </Tooltip>
                          <Tooltip content={t('reseller.admin.reject')}>
                            <button
                              onClick={() => { setRejectModalReseller(r); setRejectReason(''); }}
                              className="rounded p-1 text-red-500 hover:bg-red-50 hover:text-red-600"
                              aria-label={t('reseller.admin.reject')}
                            >
                              <XCircle className="h-4 w-4" />
                            </button>
                          </Tooltip>
                        </div>
                      ) : (
                        <>
                          <Tooltip content={t('reseller.admin.view')}>
                            <button onClick={() => setDetailReseller(r)} className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground" aria-label={t('reseller.admin.view')}>
                              <Eye className="h-4 w-4" />
                            </button>
                          </Tooltip>
                          <Tooltip content={t('common.edit')}>
                            <button onClick={() => openEdit(r)} className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground" aria-label={t('common.edit')}>
                              <Edit className="h-4 w-4" />
                            </button>
                          </Tooltip>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">{t('common.total', { count: String(data?.total ?? 0) })}</p>
              <div className="flex gap-1">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="rounded border border-border px-3 py-1 text-sm disabled:opacity-50">{t('common.prev')}</button>
                <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="rounded border border-border px-3 py-1 text-sm disabled:opacity-50">{t('common.next')}</button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Create Modal */}
      {createOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button type="button" className="absolute inset-0 bg-black/40" onClick={() => setCreateOpen(false)} aria-label={t('common.close')} />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground">{t('reseller.admin.create_title')}</h3>
              <button onClick={() => setCreateOpen(false)} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label htmlFor="create-email" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.admin.col_email')}</label>
                <input id="create-email" type="email" value={createEmail} onChange={(e) => setCreateEmail(e.target.value)} required className="w-full" placeholder="partner@example.com" />
              </div>
              <div>
                <label htmlFor="create-name" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.admin.col_name')}</label>
                <input id="create-name" type="text" value={createName} onChange={(e) => setCreateName(e.target.value)} required className="w-full" placeholder="Partner Inc" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="create-commission" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.admin.col_commission')} (%)</label>
                  <input id="create-commission" type="number" min="0" max="100" value={createCommission} onChange={(e) => setCreateCommission(e.target.value)} required className="w-full" />
                </div>
                <div>
                  <label htmlFor="create-payout" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.admin.col_min_payout')} ($)</label>
                  <input id="create-payout" type="number" min="1" value={createMinPayout} onChange={(e) => setCreateMinPayout(e.target.value)} required className="w-full" />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setCreateOpen(false)} className="rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground hover:bg-secondary">{t('common.cancel')}</button>
                <button type="submit" disabled={createMutation.isPending} className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                  {createMutation.isPending ? t('common.working') : t('common.create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editReseller && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button type="button" className="absolute inset-0 bg-black/40" onClick={() => setEditReseller(null)} aria-label={t('common.close')} />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground">{t('reseller.admin.edit_title')}</h3>
              <button onClick={() => setEditReseller(null)} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleEdit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="edit-name" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.admin.col_name')}</label>
                  <input id="edit-name" type="text" value={editName} onChange={(e) => setEditName(e.target.value)} required className="w-full" />
                </div>
                <div>
                  <label htmlFor="edit-email" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.admin.col_email')}</label>
                  <input id="edit-email" type="email" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} required className="w-full" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="edit-company-name" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.profile.company_name')}</label>
                  <input id="edit-company-name" type="text" value={editCompanyName} onChange={(e) => setEditCompanyName(e.target.value)} className="w-full" placeholder="—" />
                </div>
                <div>
                  <label htmlFor="edit-tax-id" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.profile.tax_id')}</label>
                  <input id="edit-tax-id" type="text" value={editTaxId} onChange={(e) => setEditTaxId(e.target.value)} className="w-full" placeholder="—" />
                </div>
              </div>
              <div>
                <label htmlFor="edit-referral" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.admin.col_referral')}</label>
                <input id="edit-referral" type="text" value={editReferralCode} onChange={(e) => setEditReferralCode(e.target.value)} required className="w-full font-mono" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="edit-commission" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.admin.col_commission')} (%)</label>
                  <input id="edit-commission" type="number" min="0" max="100" value={editCommission} onChange={(e) => setEditCommission(e.target.value)} className="w-full" />
                </div>
                <div>
                  <label htmlFor="edit-payout" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.admin.col_min_payout')} ($)</label>
                  <input id="edit-payout" type="number" min="1" value={editMinPayout} onChange={(e) => setEditMinPayout(e.target.value)} className="w-full" />
                </div>
              </div>
              <div>
                <label htmlFor="edit-status" className="block mb-1.5 text-sm text-muted-foreground">{t('common.status')}</label>
                <select id="edit-status" value={editStatus} onChange={(e) => setEditStatus(e.target.value)} className="w-full rounded-md border border-border bg-card px-3 py-1.5 text-sm">
                  <option value="pending">Pending</option>
                  <option value="active">Active</option>
                  <option value="suspended">Suspended</option>
                  <option value="deactivated">Deactivated</option>
                </select>
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setEditReseller(null)} className="rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground hover:bg-secondary">{t('common.cancel')}</button>
                <button type="submit" disabled={updateMutation.isPending} className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                  {updateMutation.isPending ? t('common.saving') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {rejectModalReseller && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button type="button" className="absolute inset-0 bg-black/40" onClick={() => setRejectModalReseller(null)} aria-label={t('common.close')} />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground">{t('reseller.admin.reject')} — {rejectModalReseller.name}</h3>
              <button onClick={() => setRejectModalReseller(null)} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                rejectMutation.mutate({ id: rejectModalReseller.id, reason: rejectReason || null });
              }}
              className="space-y-4"
            >
              <div>
                <label htmlFor="reject-reason" className="block mb-1.5 text-sm text-muted-foreground">{t('reseller.admin.reject_reason')}</label>
                <textarea
                  id="reject-reason"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="w-full rounded-md border border-border bg-card px-3 py-2 text-sm"
                  rows={3}
                  placeholder={t('reseller.admin.reject_reason')}
                />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setRejectModalReseller(null)} className="rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground hover:bg-secondary">{t('common.cancel')}</button>
                <button type="submit" disabled={rejectMutation.isPending} className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50">
                  {rejectMutation.isPending ? t('common.working') : t('reseller.admin.reject')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {detailReseller && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button type="button" className="absolute inset-0 bg-black/40" onClick={() => setDetailReseller(null)} aria-label={t('common.close')} />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground">{t('reseller.admin.detail_title')}</h3>
              <button onClick={() => setDetailReseller(null)} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
            </div>
            <div className="grid gap-3 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div><p className="text-xs text-muted-foreground">{t('reseller.admin.col_name')}</p><p className="font-medium">{detailReseller.name}</p></div>
                <div><p className="text-xs text-muted-foreground">{t('reseller.admin.col_email')}</p><p>{detailReseller.email}</p></div>
                <div><p className="text-xs text-muted-foreground">{t('reseller.admin.col_commission')}</p><p>{detailReseller.commission_pct}%</p></div>
                <div><p className="text-xs text-muted-foreground">{t('reseller.admin.col_min_payout')}</p><p>${(detailReseller.min_payout_cents / 100).toFixed(2)}</p></div>
                <div><p className="text-xs text-muted-foreground">{t('reseller.admin.col_referral')}</p><p className="font-mono">{detailReseller.referral_code}</p></div>
                <div><p className="text-xs text-muted-foreground">{t('common.status')}</p><StatusBadge status={detailReseller.status} /></div>
                <div><p className="text-xs text-muted-foreground">{t('reseller.profile.company_name')}</p><p>{detailReseller.company_name || t('common.na')}</p></div>
                <div><p className="text-xs text-muted-foreground">{t('reseller.profile.tax_id')}</p><p>{detailReseller.tax_id || t('common.na')}</p></div>
              </div>
              <div className="flex justify-end pt-2">
                <button onClick={() => setDetailReseller(null)} className="rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground hover:bg-secondary">{t('common.close')}</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
