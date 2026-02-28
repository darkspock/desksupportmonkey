import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Pagination } from '../../components/ui/Pagination';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { formatDateTime, formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';
import type { ChangeRequest, PaginatedResponse } from '../../types';

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  draft: 'default',
  pending_approval: 'info',
  scheduled: 'info',
  in_progress: 'info',
  implemented: 'info',
  closed: 'success',
  rejected: 'danger',
  rolled_back: 'danger',
};

const typeVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  standard: 'default',
  normal: 'info',
  emergency: 'danger',
};

interface FormValues {
  title: string;
  change_type: string;
  planned_date: string;
  rollback_plan: string;
}

const EMPTY_FORM: FormValues = { title: '', change_type: 'standard', planned_date: '', rollback_plan: '' };
const TYPES_REQUIRING_ROLLBACK = ['normal', 'emergency'];

export default function ChangeListPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formValues, setFormValues] = useState<FormValues>(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const pageSize = 20;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['changes', page, search, statusFilter, typeFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', String(pageSize));
      if (search) params.set('search', search);
      if (statusFilter) params.set('status', statusFilter);
      if (typeFilter) params.set('type', typeFilter);
      const { data } = await api.get(`/changes?${params}`);
      return data as PaginatedResponse<ChangeRequest>;
    },
  });

  const create = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        title: formValues.title.trim(),
        change_type: formValues.change_type,
      };
      if (formValues.planned_date) payload.planned_date = formValues.planned_date;
      if (formValues.rollback_plan.trim()) payload.rollback_plan = formValues.rollback_plan.trim();
      const { data } = await api.post('/changes', payload);
      return data as { id: string };
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      setShowForm(false);
      setFormValues(EMPTY_FORM);
      setFormError('');
      showToast({ title: t('page.changes.toast_created'), variant: 'success' });
      navigate(`/changes/${data.id}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error creating change request';
      setFormError(detail);
      showToast({ title: t('page.changes.error_create'), description: detail, variant: 'error' });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formValues.title.trim()) {
      setFormError('Title is required');
      return;
    }
    setFormError('');
    create.mutate();
  };

  const selectClasses = 'h-9 rounded-md border border-border bg-card px-3 text-sm text-foreground';
  const inputClasses = 'w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring';

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.changes.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.changes.subtitle')}</p>
        </div>
        <button
          onClick={() => { setShowForm(true); setFormValues(EMPTY_FORM); setFormError(''); }}
          className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.changes.add')}
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder={t('page.changes.search_placeholder')}
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className={`${selectClasses} w-64`}
        />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className={selectClasses}>
          <option value="">{t('page.changes.filter_status')}</option>
          <option value="draft">{t('enum.change_status.draft')}</option>
          <option value="pending_approval">{t('enum.change_status.pending_approval')}</option>
          <option value="scheduled">{t('enum.change_status.scheduled')}</option>
          <option value="in_progress">{t('enum.change_status.in_progress')}</option>
          <option value="implemented">{t('enum.change_status.implemented')}</option>
          <option value="closed">{t('enum.change_status.closed')}</option>
          <option value="rejected">{t('enum.change_status.rejected')}</option>
          <option value="rolled_back">{t('enum.change_status.rolled_back')}</option>
        </select>
        <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }} className={selectClasses}>
          <option value="">{t('page.changes.filter_type')}</option>
          <option value="standard">{t('enum.change_type.standard')}</option>
          <option value="normal">{t('enum.change_type.normal')}</option>
          <option value="emergency">{t('enum.change_type.emergency')}</option>
        </select>
      </div>

      {isLoading && <Loading />}
      {isError && <ErrorState message={(error as Error).message} onRetry={refetch} />}

      {data && data.data.length === 0 && (
        <EmptyState message={t('page.changes.no_results')} />
      )}

      {data && data.data.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  <th className="px-4 py-3">{t('page.changes.col_title')}</th>
                  <th className="px-4 py-3">{t('page.changes.col_type')}</th>
                  <th className="px-4 py-3">{t('page.changes.col_status')}</th>
                  <th className="px-4 py-3">{t('page.changes.col_planned_date')}</th>
                  <th className="px-4 py-3">{t('page.changes.col_assigned_to')}</th>
                  <th className="px-4 py-3">{t('page.changes.col_created')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.data.map((c) => (
                  <tr key={c.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-medium">
                      <Link to={`/changes/${c.id}`} className="text-primary hover:underline">
                        {c.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={typeVariant[c.change_type] || 'default'}>
                        {t(`enum.change_type.${c.change_type}`)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusVariant[c.status] || 'default'}>
                        {t(`enum.change_status.${c.status}`)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {c.planned_date ? formatDate(c.planned_date) : '—'}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {c.assigned_to_name || '—'}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {c.created_at ? formatDateTime(c.created_at) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={data.meta.page}
            pageSize={data.meta.page_size}
            total={data.meta.total}
            onChange={setPage}
          />
        </>
      )}

      {/* Create Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold text-foreground">{t('page.changes.add')}</h3>
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.changes.field_title')} *</label>
                <input
                  value={formValues.title}
                  onChange={(e) => setFormValues({ ...formValues, title: e.target.value })}
                  className={inputClasses}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.change_type')}</label>
                <select
                  value={formValues.change_type}
                  onChange={(e) => setFormValues({ ...formValues, change_type: e.target.value })}
                  className={inputClasses}
                >
                  <option value="standard">{t('enum.change_type.standard')}</option>
                  <option value="normal">{t('enum.change_type.normal')}</option>
                  <option value="emergency">{t('enum.change_type.emergency')}</option>
                </select>
              </div>
              {TYPES_REQUIRING_ROLLBACK.includes(formValues.change_type) && (
                <div>
                  <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.rollback_plan')} *</label>
                  <textarea
                    value={formValues.rollback_plan}
                    onChange={(e) => setFormValues({ ...formValues, rollback_plan: e.target.value })}
                    className={inputClasses}
                    rows={2}
                    required
                  />
                </div>
              )}
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.changes.field_planned_date')}</label>
                <input
                  type="datetime-local"
                  value={formValues.planned_date}
                  onChange={(e) => setFormValues({ ...formValues, planned_date: e.target.value })}
                  className={inputClasses}
                />
              </div>
              {formError && <p className="text-sm text-destructive">{formError}</p>}
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={create.isPending}
                  className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
                >
                  {create.isPending ? t('common.saving') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
