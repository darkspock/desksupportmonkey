import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { EmployeeSearchSelect } from '../../components/ui/EmployeeSearchSelect';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';
import { formatDateTime } from '../../lib/date';
import { useToast } from '../../hooks/useToast';
import type { AssignableUser, MaintenanceRecord, PaginatedResponse, User } from '../../types';

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  scheduled: 'info',
  in_progress: 'warning',
  completed: 'success',
  cancelled: 'default',
  skipped: 'default',
};

export default function MaintenanceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { t } = useI18n();
  const { showToast } = useToast();
  const [assignUserId, setAssignUserId] = useState('');
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [reason, setReason] = useState('');
  const [completeNotes, setCompleteNotes] = useState('');
  const [findings, setFindings] = useState('');
  const [pendingReasonAction, setPendingReasonAction] = useState<'cancel' | 'skip' | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['maintenance', id],
    queryFn: async () => (await api.get(`/maintenance/${id}`)).data.data as MaintenanceRecord,
    enabled: Boolean(id),
  });

  const { data: techniciansData } = useQuery({
    queryKey: ['maintenance-detail-technicians-options'],
    queryFn: async () => {
      const { data } = await api.get('/users', { params: { page: 1, page_size: 100, role: 'technician' } });
      return data as PaginatedResponse<User>;
    },
  });

  const technicians = techniciansData?.data ?? [];
  const technicianById = new Map(technicians.map((tech) => [tech.id, tech.email]));
  const technicianOptions: AssignableUser[] = technicians
    .filter((tech) => tech.is_active)
    .map((tech) => ({ id: tech.id, email: tech.email, name: tech.name }));

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['maintenance', id] });
    queryClient.invalidateQueries({ queryKey: ['maintenance'] });
    queryClient.invalidateQueries({ queryKey: ['my-maintenance'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-maintenance'] });
  };

  const errorDetail = (err: unknown) =>
    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.maintenance_detail.error_action');

  const assign = useMutation({
    mutationFn: () => api.post(`/maintenance/${id}/assign`, { technician_id: assignUserId }),
    onSuccess: () => { invalidate(); showToast({ title: t('page.maintenance_detail.toast_assigned'), variant: 'success' }); setAssignUserId(''); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const start = useMutation({
    mutationFn: () => api.post(`/maintenance/${id}/start`),
    onSuccess: () => { invalidate(); showToast({ title: t('page.maintenance_detail.toast_started'), variant: 'success' }); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const complete = useMutation({
    mutationFn: () => api.post(`/maintenance/${id}/complete`, { completion_notes: completeNotes || null, actual_findings: findings || null }),
    onSuccess: () => { invalidate(); showToast({ title: t('page.maintenance_detail.toast_completed'), variant: 'success' }); setCompleteNotes(''); setFindings(''); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const cancel = useMutation({
    mutationFn: () => api.post(`/maintenance/${id}/cancel`, { reason }),
    onSuccess: () => { invalidate(); showToast({ title: t('page.maintenance_detail.toast_cancelled'), variant: 'success' }); setReason(''); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const skip = useMutation({
    mutationFn: () => api.post(`/maintenance/${id}/skip`, { reason }),
    onSuccess: () => { invalidate(); showToast({ title: t('page.maintenance_detail.toast_skipped'), variant: 'success' }); setReason(''); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail} onRetry={() => { void refetch(); }} />;
  if (!data) return <ErrorState message={t('page.maintenance_detail.not_found')} />;

  const statusKey = data.status.toLowerCase();
  const canStart = data.status === 'SCHEDULED';
  const canComplete = data.status === 'IN_PROGRESS';
  const canEdit = data.status === 'SCHEDULED';
  const canCancel = data.status === 'SCHEDULED' || data.status === 'IN_PROGRESS';
  const canSkip = data.status === 'SCHEDULED';
  const isClosed = data.status === 'COMPLETED' || data.status === 'CANCELLED' || data.status === 'SKIPPED';
  const technicianLabel = data.technician_id ? technicianById.get(data.technician_id) || data.technician_id : '—';
  const hasMainContent = Boolean(
    data.description
      || data.checklist_items.length > 0
      || data.completion_notes
      || data.actual_findings,
  );

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t('page.maintenance.title')} / {t('page.maintenance_detail.page_title')}
          </p>
          <p className="text-sm text-muted-foreground">{t('page.maintenance_detail.page_subtitle')}</p>
        </div>
        <button onClick={() => navigate('/maintenance')} className="rounded-md border bg-background px-3 py-1.5 text-sm hover:bg-accent transition-colors">
          {t('page.maintenance_detail.back_to_list')}
        </button>
      </div>

      <Card>
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">{data.title}</h2>
            <p className="mt-1 font-mono text-xs text-muted-foreground">{data.id}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={statusVariant[statusKey] || 'default'}>{t(`enum.maintenance_status.${statusKey}`)}</Badge>
            {canEdit ? (
              <Link to={`/maintenance/${data.id}/edit`} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
                {t('common.edit')}
              </Link>
            ) : (
              <button type="button" disabled title={t('page.maintenance_detail.edit_disabled')} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs disabled:pointer-events-none disabled:opacity-50">
                {t('common.edit')}
              </button>
            )}
          </div>
        </div>

        {data.description && (
          <div className="rounded-lg border border-border bg-secondary p-3 text-sm text-foreground">
            {data.description}
          </div>
        )}
      </Card>

      <div className={`grid grid-cols-1 gap-5 ${hasMainContent ? 'xl:grid-cols-3' : 'lg:grid-cols-2'}`}>
        <div className={`space-y-5 ${hasMainContent ? 'xl:col-span-2' : ''}`}>
          <Card>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.maintenance_detail.overview')}</h3>
            <div className="space-y-2 text-sm">
              <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('table.priority')}</p>
                <p className="mt-1 font-medium text-foreground">{t(`enum.maintenance_priority.${data.priority.toLowerCase()}`)}</p>
              </div>
              <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('table.technician')}</p>
                <p className="mt-1 text-foreground">{technicianLabel}</p>
              </div>
              <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('table.asset')}</p>
                <p className="mt-1 font-mono text-xs text-foreground">{data.asset_id}</p>
              </div>
              <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('table.date')}</p>
                <p className="mt-1 text-foreground">{data.scheduled_at ? formatDateTime(data.scheduled_at) : '—'}</p>
              </div>
              {data.started_at && (
                <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('page.maintenance_detail.started_at')}</p>
                  <p className="mt-1 text-foreground">{formatDateTime(data.started_at)}</p>
                </div>
              )}
              {data.completed_at && (
                <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('page.maintenance_detail.completed_at')}</p>
                  <p className="mt-1 text-foreground">{formatDateTime(data.completed_at)}</p>
                </div>
              )}
            </div>
          </Card>

          {hasMainContent && (
            <>
              {data.checklist_items.length > 0 && (
                <Card>
                  <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.maintenance_detail.checklist')}</h3>
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {data.checklist_items.map((item, idx) => (
                      <div key={`${item}-${idx}`} className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground">
                        {item}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {(data.completion_notes || data.actual_findings) && (
                <Card>
                  <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.maintenance_detail.complete')}</h3>
                  {data.completion_notes && (
                    <div className="mb-3 rounded-lg border border-border bg-card p-3 text-sm text-foreground">
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t('page.maintenance_detail.completion_notes')}</p>
                      <p>{data.completion_notes}</p>
                    </div>
                  )}
                  {data.actual_findings && (
                    <div className="rounded-lg border border-border bg-card p-3 text-sm text-foreground">
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t('page.maintenance_detail.actual_findings')}</p>
                      <p>{data.actual_findings}</p>
                    </div>
                  )}
                </Card>
              )}
            </>
          )}
        </div>

        <div className={`space-y-5 ${hasMainContent ? '' : 'lg:col-start-2'}`}>

          <Card>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('table.actions')}</h3>
            {!isClosed && (
              <div className="mb-4 flex flex-wrap justify-end gap-2">
                {canStart && (
                  <button
                    onClick={() => setAssignModalOpen(true)}
                    className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                  >
                    {t('page.maintenance_detail.assign')}
                  </button>
                )}
                {canStart && (
                  <button onClick={() => start.mutate()} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50" disabled={start.isPending}>
                    {t('page.maintenance_detail.start')}
                  </button>
                )}
                {canComplete && (
                  <button onClick={() => complete.mutate()} className="rounded-md h-9 px-4 text-sm font-medium bg-success text-white shadow-xs hover:bg-success/90 disabled:opacity-50" disabled={complete.isPending}>
                    {t('page.maintenance_detail.complete')}
                  </button>
                )}
                {canCancel && (
                  <button
                    onClick={() => {
                      setPendingReasonAction('cancel');
                    }}
                    className="rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50"
                    disabled={cancel.isPending}
                  >
                    {t('page.maintenance_detail.cancel')}
                  </button>
                )}
                {canSkip && (
                  <button
                    onClick={() => {
                      setPendingReasonAction('skip');
                    }}
                    className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                    disabled={skip.isPending}
                  >
                    {t('page.maintenance_detail.skip')}
                  </button>
                )}
              </div>
            )}

            {canComplete && (
              <div className="rounded-lg border border-border p-3">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t('page.maintenance_detail.complete')}</p>
                <div className="grid grid-cols-1 gap-2">
                  <textarea
                    value={completeNotes}
                    onChange={(e) => setCompleteNotes(e.target.value)}
                    rows={2}
                    placeholder={t('page.maintenance_detail.completion_notes')}
                    className="w-full"
                  />
                  <textarea
                    value={findings}
                    onChange={(e) => setFindings(e.target.value)}
                    rows={2}
                    placeholder={t('page.maintenance_detail.actual_findings')}
                    className="w-full"
                  />
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>

      {pendingReasonAction && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (!cancel.isPending && !skip.isPending) setPendingReasonAction(null);
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">
              {pendingReasonAction === 'cancel' ? t('page.maintenance_detail.cancel') : t('page.maintenance_detail.skip')}
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">{t('page.maintenance_detail.reason_modal_desc')}</p>

            <div className="mt-4 space-y-3">
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder={t('page.maintenance_detail.reason_placeholder')}
                rows={3}
                className="w-full"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setPendingReasonAction(null)}
                  disabled={cancel.isPending || skip.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (!reason.trim()) {
                      showToast({ title: t('page.maintenance_detail.reason_required'), variant: 'error' });
                      return;
                    }
                    if (pendingReasonAction === 'cancel') {
                      cancel.mutate(undefined, { onSettled: () => setPendingReasonAction(null) });
                    } else {
                      skip.mutate(undefined, { onSettled: () => setPendingReasonAction(null) });
                    }
                  }}
                  disabled={cancel.isPending || skip.isPending}
                  className={`inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium text-white shadow-xs disabled:opacity-50 ${
                    pendingReasonAction === 'cancel' ? 'bg-destructive hover:bg-destructive/90' : 'bg-primary hover:bg-primary/90'
                  }`}
                >
                  {(cancel.isPending || skip.isPending)
                    ? t('common.working')
                    : pendingReasonAction === 'cancel'
                      ? t('page.maintenance_detail.cancel')
                      : t('page.maintenance_detail.skip')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {assignModalOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (!assign.isPending) setAssignModalOpen(false);
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.maintenance_detail.assign')}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{t('page.maintenance_detail.assign_modal_desc')}</p>

            <div className="mt-4 space-y-3">
              <EmployeeSearchSelect
                users={technicianOptions}
                value={assignUserId}
                onChange={setAssignUserId}
                placeholder={t('page.maintenance_detail.assign_placeholder')}
                allLabel={t('page.asset_list.all_assignees')}
                noResultsLabel={t('page.asset_list.no_assignee_results')}
                className="w-full"
              />

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setAssignModalOpen(false)}
                  disabled={assign.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (!assignUserId.trim()) {
                      showToast({ title: t('page.maintenance_detail.assign_placeholder'), variant: 'error' });
                      return;
                    }
                    assign.mutate(undefined, {
                      onSuccess: () => setAssignModalOpen(false),
                    });
                  }}
                  disabled={assign.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {assign.isPending ? t('common.working') : t('page.maintenance_detail.assign')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
