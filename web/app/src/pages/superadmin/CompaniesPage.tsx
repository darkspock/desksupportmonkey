import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { Tooltip } from '../../components/ui/Tooltip';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { Company, CompanyStatus, PaginatedResponse } from '../../types';
import { CompanyBillingModal } from './CompanyBillingModal';

/* Icons – Heroicons-style outline SVGs (24×24, strokeWidth 1.5) */
const icon = (d: string) => (
  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);

const PencilIcon = icon('m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125');
const CreditCardIcon = icon('M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Z');
const ArrowPathIcon = icon('M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182');
const PlusIcon = icon('M12 4.5v15m7.5-7.5h-15');
const XIcon = icon('M6 18 18 6M6 6l12 12');

/* ─── Shared button styles ──────────────────────────────────────────── */
const btnPrimary = 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50 transition-all';
const btnOutline = 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground disabled:opacity-50 transition-all';
const btnDanger = 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50 transition-all';
const btnWarning = 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-yellow-500 text-white shadow-xs hover:bg-yellow-600 disabled:opacity-50 transition-all';
const btnIcon = 'inline-flex items-center justify-center rounded-md h-8 w-8 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors';

/* ─── Plan badge colors ─────────────────────────────────────────────── */
const planColors: Record<string, string> = {
  free: 'bg-muted text-muted-foreground',
  premium: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  enterprise: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  open_source: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
};

/* ═══════════════════════════════════════════════════════════════════════
   Create Company Dialog
   ═══════════════════════════════════════════════════════════════════════ */
interface CreateDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

function CompanyCreateDialog({ open, onClose, onSuccess }: CreateDialogProps) {
  const { t } = useI18n();
  const { showToast } = useToast();
  const [form, setForm] = useState({ name: '', admin_email: '', email_domains: '' });
  const [error, setError] = useState('');

  const create = useMutation({
    mutationFn: () => api.post('/companies', {
      name: form.name,
      admin_email: form.admin_email,
      email_domains: form.email_domains.split(',').map((d) => d.trim()).filter(Boolean),
    }),
    onSuccess: () => {
      setForm({ name: '', admin_email: '', email_domains: '' });
      setError('');
      showToast({ title: t('page.companies.toast_created'), variant: 'success' });
      onSuccess();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.companies.error_generic');
      setError(detail);
      showToast({ title: t('page.companies.error_create_title'), description: detail, variant: 'error' });
    },
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
      <button type="button" className="absolute inset-0 bg-black/40" onClick={onClose} aria-label={t('common.close')} />
      <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">{t('page.companies.new')}</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground" aria-label={t('common.close')}>{XIcon}</button>
        </div>
        <form onSubmit={(e) => { e.preventDefault(); create.mutate(); }} className="space-y-3">
          {error && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{error}</div>}
          <div>
            <label className="block mb-1.5 text-sm text-muted-foreground">{t('table.company_name')}</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className="w-full" />
          </div>
          <div>
            <label className="block mb-1.5 text-sm text-muted-foreground">{t('auth.register.admin_email')}</label>
            <input type="email" value={form.admin_email} onChange={(e) => setForm({ ...form, admin_email: e.target.value })} required className="w-full" />
          </div>
          <div>
            <label className="block mb-1.5 text-sm text-muted-foreground">{t('table.email_domains')}</label>
            <input value={form.email_domains} onChange={(e) => setForm({ ...form, email_domains: e.target.value })} placeholder={t('common.placeholder_domains_short')} className="w-full" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className={btnOutline}>{t('common.cancel')}</button>
            <button type="submit" disabled={create.isPending} className={btnPrimary}>
              {create.isPending ? t('page.companies.creating') : t('page.companies.create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   Edit Company Dialog (name + domains only)
   ═══════════════════════════════════════════════════════════════════════ */
interface EditDialogProps {
  company: { id: string; name: string; email_domains: string } | null;
  onClose: () => void;
  onSuccess: () => void;
}

function CompanyEditDialog({ company, onClose, onSuccess }: EditDialogProps) {
  const { t } = useI18n();
  const { showToast } = useToast();
  const [name, setName] = useState(company?.name ?? '');
  const [emailDomains, setEmailDomains] = useState(company?.email_domains ?? '');

  const updateCompany = useMutation({
    mutationFn: () =>
      api.put(`/companies/${company!.id}`, {
        name,
        email_domains: emailDomains.split(',').map((d) => d.trim()).filter(Boolean),
      }),
    onSuccess: () => {
      showToast({ title: t('page.companies.toast_updated'), variant: 'success' });
      onSuccess();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.companies.error_update');
      showToast({ title: t('page.companies.error_update_title'), description: detail, variant: 'error' });
    },
  });

  if (!company) return null;

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
      <button type="button" className="absolute inset-0 bg-black/40" onClick={onClose} aria-label={t('common.close')} />
      <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">{t('page.companies.edit')}</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground" aria-label={t('common.close')}>{XIcon}</button>
        </div>
        <form onSubmit={(e) => { e.preventDefault(); updateCompany.mutate(); }} className="space-y-3">
          <div>
            <label className="block mb-1.5 text-sm text-muted-foreground">{t('table.name')}</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required className="w-full" />
          </div>
          <div>
            <label className="block mb-1.5 text-sm text-muted-foreground">{t('table.email_domains')}</label>
            <input value={emailDomains} onChange={(e) => setEmailDomains(e.target.value)} className="w-full" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className={btnOutline}>{t('common.cancel')}</button>
            <button type="submit" disabled={updateCompany.isPending || !name.trim()} className={btnPrimary}>
              {updateCompany.isPending ? t('common.saving') : t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   Change Status Dialog
   ═══════════════════════════════════════════════════════════════════════ */
interface StatusDialogProps {
  company: { id: string; name: string; status: CompanyStatus } | null;
  onClose: () => void;
  onSuccess: () => void;
}

function CompanyStatusDialog({ company, onClose, onSuccess }: StatusDialogProps) {
  const { t } = useI18n();
  const { showToast } = useToast();
  const [pendingStatus, setPendingStatus] = useState<CompanyStatus | null>(null);

  const changeStatus = useMutation({
    mutationFn: (status: CompanyStatus) =>
      api.patch(`/companies/${company!.id}/status`, { status }),
    onSuccess: (_res, status) => {
      setPendingStatus(null);
      showToast({ title: t('page.companies.toast_status_changed', { status: t(`enum.${status}`) }), variant: 'success' });
      onSuccess();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.companies.error_update');
      showToast({ title: t('page.companies.error_status_title'), description: detail, variant: 'error' });
    },
  });

  const requestChange = (status: CompanyStatus) => {
    if (status === 'suspended' || status === 'deactivated') {
      setPendingStatus(status);
    } else {
      changeStatus.mutate(status);
    }
  };

  if (!company) return null;

  return (
    <>
      <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
        <button type="button" className="absolute inset-0 bg-black/40" onClick={onClose} aria-label={t('common.close')} />
        <div className="relative z-[91] w-full max-w-sm rounded-xl border border-border bg-card p-6 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground">{t('page.companies.change_status')}</h3>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground" aria-label={t('common.close')}>{XIcon}</button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">{company.name}</span>
            <StatusBadge status={company.status} />
          </div>

          <div className="flex flex-wrap justify-end gap-2">
            {company.status !== 'active' && (
              <button onClick={() => requestChange('active')} disabled={changeStatus.isPending} className={btnPrimary}>
                {t('page.companies.action_activate')}
              </button>
            )}
            {company.status === 'active' && (
              <button onClick={() => requestChange('suspended')} disabled={changeStatus.isPending} className={btnWarning}>
                {t('page.companies.action_suspend')}
              </button>
            )}
            {company.status !== 'deactivated' && (
              <button onClick={() => requestChange('deactivated')} disabled={changeStatus.isPending} className={btnDanger}>
                {t('page.companies.action_deactivate')}
              </button>
            )}
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={Boolean(pendingStatus)}
        title={t('page.companies.confirm_status_title')}
        description={pendingStatus ? t('page.companies.confirm_status_desc', { name: company.name, status: t(`enum.${pendingStatus}`) }) : ''}
        confirmLabel={t('common.confirm')}
        tone="danger"
        busy={changeStatus.isPending}
        onCancel={() => setPendingStatus(null)}
        onConfirm={() => {
          if (pendingStatus) changeStatus.mutate(pendingStatus);
        }}
      />
    </>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   Companies Page
   ═══════════════════════════════════════════════════════════════════════ */
export default function CompaniesPage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [planFilter, setPlanFilter] = useState('');
  const [inTrialFilter, setInTrialFilter] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [editingCompany, setEditingCompany] = useState<{ id: string; name: string; email_domains: string } | null>(null);
  const [statusCompany, setStatusCompany] = useState<{ id: string; name: string; status: CompanyStatus } | null>(null);
  const [billingCompany, setBillingCompany] = useState<{ id: string; name: string } | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error: listError, refetch } = useQuery({
    queryKey: ['companies', page, search, planFilter, inTrialFilter],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (search) params.search = search;
      if (planFilter) params.plan = planFilter;
      if (inTrialFilter) params.in_trial = true;
      const { data } = await api.get('/companies', { params });
      return data as PaginatedResponse<Company>;
    },
  });

  const invalidateList = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['companies'] });
  }, [queryClient]);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.companies.title')}</h2>
        <button onClick={() => setShowCreate(true)} className={btnPrimary}>
          {PlusIcon}
          {t('page.companies.new')}
        </button>
      </div>

      {/* Filters */}
      <Card>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <input placeholder={t('common.search')} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="w-48" />
          <select
            value={planFilter}
            onChange={(e) => { setPlanFilter(e.target.value); setPage(1); }}
            className="text-sm rounded-md border border-input bg-background px-3 py-2"
          >
            <option value="">{t('page.companies.filter_all_plans')}</option>
            <option value="free">Free</option>
            <option value="premium">Premium</option>
            <option value="enterprise">Enterprise</option>
            <option value="open_source">Open Source</option>
          </select>
          <label className="flex items-center gap-1.5 text-sm text-muted-foreground cursor-pointer select-none">
            <input
              type="checkbox"
              checked={inTrialFilter}
              onChange={(e) => { setInTrialFilter(e.target.checked); setPage(1); }}
              className="rounded border-input"
            />
            {t('page.companies.filter_in_trial')}
          </label>
        </div>

        {/* Table */}
        {isLoading ? <Loading /> : isError ? (
          <ErrorState
            message={(listError as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => { void refetch(); }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.companies.empty')} />
        ) : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>{t('table.name')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th>{t('page.companies.plan_column')}</Th>
                  <Th>{t('table.users')}</Th>
                  <Th>{t('page.companies.assets_column')}</Th>
                  <Th className="text-right">{t('table.actions')}</Th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((c) => (
                  <tr key={c.id}>
                    <Td>
                      <span className="font-medium">{c.name}</span>
                      {c.trial_days_remaining != null && (
                        <span className="ml-2 inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                          {t('page.companies.trial_badge', { days: String(c.trial_days_remaining) })}
                        </span>
                      )}
                    </Td>
                    <Td><StatusBadge status={c.status} /></Td>
                    <Td>
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${planColors[c.plan ?? ''] ?? planColors.free}`}>
                        {c.plan ?? 'free'}
                      </span>
                    </Td>
                    <Td>{c.user_count ?? '-'}</Td>
                    <Td>{c.asset_count ?? '-'}</Td>
                    <Td>
                      <div className="flex items-center justify-end gap-1">
                        <Tooltip content={t('page.companies.edit')}>
                          <button
                            onClick={() => setEditingCompany({ id: c.id, name: c.name, email_domains: c.email_domains.join(', ') })}
                            className={btnIcon}
                            aria-label={t('page.companies.edit')}
                          >
                            {PencilIcon}
                          </button>
                        </Tooltip>
                        <Tooltip content={t('page.companies.change_status')}>
                          <button
                            onClick={() => setStatusCompany({ id: c.id, name: c.name, status: c.status })}
                            className={btnIcon}
                            aria-label={t('page.companies.change_status')}
                          >
                            {ArrowPathIcon}
                          </button>
                        </Tooltip>
                        <Tooltip content={t('page.companies.billing_action')}>
                          <button
                            onClick={() => setBillingCompany({ id: c.id, name: c.name })}
                            className={btnIcon}
                            aria-label={t('page.companies.billing_action')}
                          >
                            {CreditCardIcon}
                          </button>
                        </Tooltip>
                      </div>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </>
        )}
      </Card>

      {/* ── Dialogs ────────────────────────────────────────────────── */}

      <CompanyCreateDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onSuccess={() => { setShowCreate(false); invalidateList(); }}
      />

      <CompanyEditDialog
        company={editingCompany}
        onClose={() => setEditingCompany(null)}
        onSuccess={() => { setEditingCompany(null); invalidateList(); }}
      />

      <CompanyStatusDialog
        company={statusCompany}
        onClose={() => setStatusCompany(null)}
        onSuccess={() => { setStatusCompany(null); invalidateList(); }}
      />

      {billingCompany && (
        <CompanyBillingModal
          companyId={billingCompany.id}
          companyName={billingCompany.name}
          onClose={() => setBillingCompany(null)}
        />
      )}
    </div>
  );
}
