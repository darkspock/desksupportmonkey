import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { Company, CompanyStatus, PaginatedResponse } from '../../types';
import { CompanyBillingModal } from './CompanyBillingModal';

export default function CompaniesPage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', admin_email: '', email_domains: '' });
  const [error, setError] = useState('');
  const [pendingStatusChange, setPendingStatusChange] = useState<{ id: string; name: string; status: CompanyStatus } | null>(null);
  const [editingCompany, setEditingCompany] = useState<{ id: string; name: string; email_domains: string } | null>(null);
  const [billingCompany, setBillingCompany] = useState<{ id: string; name: string } | null>(null);
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const { data, isLoading, isError, error: listError, refetch } = useQuery({
    queryKey: ['companies', page, search],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (search) params.search = search;
      const { data } = await api.get('/companies', { params });
      return data as PaginatedResponse<Company>;
    },
  });

  const create = useMutation({
    mutationFn: () => api.post('/companies', {
      name: form.name,
      admin_email: form.admin_email,
      email_domains: form.email_domains.split(',').map((d) => d.trim()).filter(Boolean),
    }),
    onSuccess: () => {
      setForm({ name: '', admin_email: '', email_domains: '' });
      setShowForm(false);
      setError('');
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      showToast({ title: t('page.companies.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.companies.error_generic');
      setError(detail);
      showToast({ title: t('page.companies.error_create_title'), description: detail, variant: 'error' });
    },
  });

  const updateCompany = useMutation({
    mutationFn: ({ id, name, emailDomains }: { id: string; name: string; emailDomains: string[] }) =>
      api.put(`/companies/${id}`, { name, email_domains: emailDomains }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      setEditingCompany(null);
      showToast({ title: t('page.companies.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.companies.error_update');
      showToast({ title: t('page.companies.error_update_title'), description: detail, variant: 'error' });
    },
  });

  const changeStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: CompanyStatus }) =>
      api.patch(`/companies/${id}/status`, { status }),
    onSuccess: (_res, vars) => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      setPendingStatusChange(null);
      showToast({ title: t('page.companies.toast_status_changed', { status: t(`enum.${vars.status}`) }), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.companies.error_update');
      showToast({ title: t('page.companies.error_status_title'), description: detail, variant: 'error' });
    },
  });

  const requestStatusChange = (company: Company, nextStatus: string) => {
    const status = nextStatus as CompanyStatus;

    if (status === company.status) return;

    if (status === 'suspended' || status === 'deactivated') {
      setPendingStatusChange({ id: company.id, name: company.name, status });
      return;
    }

    changeStatus.mutate({ id: company.id, status });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.companies.title')}</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className={showForm
            ? 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50'
            : 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50'}
        >
          {showForm ? t('common.close') : t('page.companies.new')}
        </button>
      </div>

      {showForm && (
        <Card className="mb-4">
          <form onSubmit={(e) => { e.preventDefault(); create.mutate(); }} className="space-y-3">
            {error && <p className="text-sm text-destructive">{error}</p>}
            <div>
              <label className="block mb-1.5 text-muted-foreground">{t('table.company_name')}</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className="w-full" />
            </div>
            <div>
              <label className="block mb-1.5 text-muted-foreground">{t('auth.register.admin_email')}</label>
              <input type="email" value={form.admin_email} onChange={(e) => setForm({ ...form, admin_email: e.target.value })} required className="w-full" />
            </div>
            <div>
              <label className="block mb-1.5 text-muted-foreground">{t('table.email_domains')}</label>
              <input value={form.email_domains} onChange={(e) => setForm({ ...form, email_domains: e.target.value })} placeholder={t('common.placeholder_domains_short')} className="w-full" />
            </div>
            <button type="submit" disabled={create.isPending} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50">
              {create.isPending ? t('page.companies.creating') : t('page.companies.create')}
            </button>
          </form>
        </Card>
      )}

      {editingCompany && (
        <Card className="mb-4">
          <h3 className="text-sm font-semibold text-foreground mb-3">{t('page.companies.edit')}</h3>
          <div className="space-y-3">
            <div>
              <label className="block mb-1.5 text-muted-foreground">{t('table.name')}</label>
              <input
                value={editingCompany.name}
                onChange={(e) => setEditingCompany({ ...editingCompany, name: e.target.value })}
                className="w-full"
              />
            </div>
            <div>
              <label className="block mb-1.5 text-muted-foreground">{t('table.email_domains')}</label>
              <input
                value={editingCompany.email_domains}
                onChange={(e) => setEditingCompany({ ...editingCompany, email_domains: e.target.value })}
                className="w-full"
              />
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  const domains = editingCompany.email_domains.split(',').map((d) => d.trim()).filter(Boolean);
                  updateCompany.mutate({ id: editingCompany.id, name: editingCompany.name, emailDomains: domains });
                }}
                disabled={updateCompany.isPending || !editingCompany.name.trim()}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {updateCompany.isPending ? t('auth.set_password.saving') : t('common.save')}
              </button>
              <button onClick={() => setEditingCompany(null)} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </Card>
      )}

      <Card>
        <div className="mb-4">
          <input placeholder={t('common.search')} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="w-48" />
        </div>

        {isLoading ? <Loading /> : isError ? (
          <ErrorState
            message={(listError as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => {
              void refetch();
            }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.companies.empty')} />
        ) : (
          <>
            <Table>
              <thead><tr><Th>{t('table.name')}</Th><Th>{t('table.status')}</Th><Th>{t('page.companies.plan_column')}</Th><Th>{t('table.users')}</Th><Th>{t('table.departments')}</Th><Th>{t('table.actions')}</Th></tr></thead>
              <tbody>
                {data.data.map((c) => (
                  <tr key={c.id}>
                    <Td>{c.name}</Td>
                    <Td><StatusBadge status={c.status} /></Td>
                    <Td><span className="text-xs capitalize">{(c as { plan?: string }).plan ?? '—'}</span></Td>
                    <Td>{c.user_count ?? '-'}</Td>
                    <Td>{c.department_count ?? '-'}</Td>
                    <Td>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setEditingCompany({ id: c.id, name: c.name, email_domains: c.email_domains.join(', ') })}
                          className="text-xs text-primary hover:underline"
                        >
                          {t('common.edit')}
                        </button>
                        <select
                          value={c.status}
                          onChange={(e) => requestStatusChange(c, e.target.value)}
                          className="text-xs"
                        >
                          <option value="active">{t('enum.active')}</option>
                          <option value="suspended">{t('enum.suspended')}</option>
                          <option value="deactivated">{t('enum.deactivated')}</option>
                        </select>
                        <button
                          onClick={() => setBillingCompany({ id: c.id, name: c.name })}
                          className="text-xs text-muted-foreground hover:text-foreground hover:underline"
                        >
                          {t('page.companies.billing_action')}
                        </button>
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

      {billingCompany && (
        <CompanyBillingModal
          companyId={billingCompany.id}
          companyName={billingCompany.name}
          onClose={() => setBillingCompany(null)}
        />
      )}

      <ConfirmDialog
        open={Boolean(pendingStatusChange)}
        title={t('page.companies.confirm_status_title')}
        description={pendingStatusChange ? t('page.companies.confirm_status_desc', { name: pendingStatusChange.name, status: t(`enum.${pendingStatusChange.status}`) }) : ''}
        confirmLabel={t('common.confirm')}
        tone="danger"
        busy={changeStatus.isPending}
        onCancel={() => setPendingStatusChange(null)}
        onConfirm={() => {
          if (pendingStatusChange) {
            changeStatus.mutate({
              id: pendingStatusChange.id,
              status: pendingStatusChange.status,
            });
          }
        }}
      />
    </div>
  );
}
