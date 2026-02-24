import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';
import { formatDateTime } from '../../lib/date';
import { useToast } from '../../hooks/useToast';
import { useAuth } from '../../contexts/AuthContext';
import type { Asset, IncidentDetail as IncidentDetailType, PaginatedResponse, SingleResponse, User, Vendor } from '../../types';

const severityVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  P1: 'danger',
  P2: 'warning',
  P3: 'info',
  P4: 'default',
};

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger' | 'purple'> = {
  detected: 'danger',
  triaged: 'warning',
  contained: 'info',
  eradicated: 'purple',
  recovered: 'success',
  closed: 'default',
};

const VALID_TRANSITIONS: Record<string, string[]> = {
  detected: ['triaged', 'closed'],
  triaged: ['contained', 'closed'],
  contained: ['eradicated', 'closed'],
  eradicated: ['recovered', 'closed'],
  recovered: ['closed'],
};

const STATUSES_NEEDING_CLOSE_REASON = ['detected', 'triaged', 'contained', 'eradicated'];

const REPORT_TYPE_LABELS: Record<string, string> = {
  early_warning_24h: 'Early Warning (24h)',
  detailed_72h: 'Detailed Report (72h)',
  final_30d: 'Final Report (30d)',
};

const REPORT_STATUS_VARIANT: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  pending: 'warning',
  generated: 'info',
  submitted: 'success',
};

function formatCountdown(seconds: number): string {
  if (seconds <= 0) return 'OVERDUE';
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function countdownColor(pct: number | null | undefined): string {
  if (!pct && pct !== 0) return 'text-foreground';
  if (pct >= 100) return 'text-destructive font-bold';
  if (pct >= 90) return 'text-destructive';
  if (pct >= 75) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-green-600 dark:text-green-400';
}

function CountdownTimer({ initialSeconds, elapsedPct }: { initialSeconds: number | null; elapsedPct: number | null }) {
  const [seconds, setSeconds] = useState(initialSeconds ?? 0);

  useEffect(() => {
    setSeconds(initialSeconds ?? 0);
  }, [initialSeconds]);

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = setInterval(() => setSeconds((s) => Math.max(s - 1, 0)), 1000);
    return () => clearInterval(timer);
  }, [seconds > 0]);

  return (
    <span className={`text-lg font-bold tabular-nums ${countdownColor(elapsedPct)}`}>
      {formatCountdown(seconds)}
    </span>
  );
}

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { t } = useI18n();
  const { showToast } = useToast();

  const { user } = useAuth();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  const [closeReason, setCloseReason] = useState('');
  const [closeModalOpen, setCloseModalOpen] = useState(false);
  const [assignUserId, setAssignUserId] = useState('');
  const [newSeverity, setNewSeverity] = useState('');
  const [selectedAssetId, setSelectedAssetId] = useState('');
  const [assetImpact, setAssetImpact] = useState('');
  const [selectedVendorId, setSelectedVendorId] = useState('');
  const [vendorInvolvement, setVendorInvolvement] = useState('');
  const [pmRootCause, setPmRootCause] = useState('');
  const [pmLessons, setPmLessons] = useState('');
  const [pmActions, setPmActions] = useState('');
  const [pmEditing, setPmEditing] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['incident', id],
    queryFn: async () => (await api.get(`/incidents/${id}`)).data as SingleResponse<IncidentDetailType>,
    enabled: Boolean(id),
  });

  const { data: techniciansData } = useQuery({
    queryKey: ['incident-technicians-options'],
    queryFn: async () => {
      const { data } = await api.get('/users', { params: { page: 1, page_size: 100, role: 'technician' } });
      return data as PaginatedResponse<User>;
    },
  });

  const technicians = techniciansData?.data ?? [];

  const { data: assetsData } = useQuery({
    queryKey: ['assets-for-linking'],
    queryFn: async () => {
      const { data } = await api.get('/assets', { params: { page: 1, page_size: 500 } });
      return data as PaginatedResponse<Asset>;
    },
  });
  const allAssets = assetsData?.data ?? [];

  const { data: vendorsData } = useQuery({
    queryKey: ['vendors-for-linking'],
    queryFn: async () => {
      const { data } = await api.get('/vendors', { params: { page: 1, page_size: 500 } });
      return data as PaginatedResponse<Vendor>;
    },
  });
  const allVendors = vendorsData?.data ?? [];

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['incident', id] });
    queryClient.invalidateQueries({ queryKey: ['incidents'] });
  };

  const errorDetail = (err: unknown) =>
    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.incident_detail.error_action');

  const changeStatus = useMutation({
    mutationFn: (payload: { status: string; close_reason?: string }) =>
      api.post(`/incidents/${id}/status`, payload),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_status_changed'), variant: 'success' }); setCloseModalOpen(false); setCloseReason(''); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const changeSeverity = useMutation({
    mutationFn: (sev: string) => api.post(`/incidents/${id}/severity`, { severity: sev }),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_severity_changed'), variant: 'success' }); setNewSeverity(''); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const assignIncident = useMutation({
    mutationFn: (userId: string) => api.post(`/incidents/${id}/assign`, { user_id: userId }),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_assigned'), variant: 'success' }); setAssignUserId(''); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const generateReport = useMutation({
    mutationFn: (reportId: string) => api.post(`/incidents/${id}/reports/${reportId}/generate`),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_report_generating'), variant: 'success' }); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const submitReport = useMutation({
    mutationFn: (reportId: string) => api.post(`/incidents/${id}/reports/${reportId}/submit`),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_report_submitted'), variant: 'success' }); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const downloadReport = async (reportId: string) => {
    try {
      const { data: resp } = await api.get(`/incidents/${id}/reports/${reportId}/download`);
      const url = (resp as { data: { download_url: string } }).data.download_url;
      window.open(url, '_blank');
    } catch (err: unknown) {
      showToast({ title: errorDetail(err), variant: 'error' });
    }
  };

  const linkAsset = useMutation({
    mutationFn: (payload: { asset_id: string; impact_description?: string }) =>
      api.post(`/incidents/${id}/assets`, payload),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_asset_linked'), variant: 'success' }); setSelectedAssetId(''); setAssetImpact(''); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const unlinkAsset = useMutation({
    mutationFn: (assetId: string) => api.delete(`/incidents/${id}/assets/${assetId}`),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_asset_unlinked'), variant: 'success' }); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const linkVendor = useMutation({
    mutationFn: (payload: { vendor_id: string; involvement_description?: string }) =>
      api.post(`/incidents/${id}/vendors`, payload),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_vendor_linked'), variant: 'success' }); setSelectedVendorId(''); setVendorInvolvement(''); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const unlinkVendor = useMutation({
    mutationFn: (vendorId: string) => api.delete(`/incidents/${id}/vendors/${vendorId}`),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_vendor_unlinked'), variant: 'success' }); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const createPostMortem = useMutation({
    mutationFn: (payload: { root_cause: string; lessons_learned: string; corrective_actions: string }) =>
      api.post(`/incidents/${id}/post-mortem`, payload),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_postmortem_created'), variant: 'success' }); setPmRootCause(''); setPmLessons(''); setPmActions(''); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  const updatePostMortem = useMutation({
    mutationFn: (payload: { root_cause?: string; lessons_learned?: string; corrective_actions?: string }) =>
      api.put(`/incidents/${id}/post-mortem`, payload),
    onSuccess: () => { invalidate(); showToast({ title: t('page.incident_detail.toast_postmortem_updated'), variant: 'success' }); setPmEditing(false); },
    onError: (err: unknown) => showToast({ title: errorDetail(err), variant: 'error' }),
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail} onRetry={() => { void refetch(); }} />;
  if (!data?.data) return <ErrorState message={t('page.incident_detail.not_found')} />;

  const incident = data.data;
  const isClosed = incident.status === 'closed';
  const isRecoveredOrClosed = incident.status === 'recovered' || incident.status === 'closed';
  const nextStatuses = VALID_TRANSITIONS[incident.status] || [];
  const needsCloseReason = STATUSES_NEEDING_CLOSE_REASON.includes(incident.status);

  const handleStatusChange = (newStatus: string) => {
    if (newStatus === 'closed' && needsCloseReason) {
      setCloseModalOpen(true);
      return;
    }
    changeStatus.mutate({ status: newStatus });
  };

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t('page.incidents.title')} / {t('page.incident_detail.page_title')}
          </p>
          <p className="text-sm text-muted-foreground">{t('page.incident_detail.page_subtitle')}</p>
        </div>
        <button onClick={() => navigate('/incidents')} className="rounded-md border bg-background px-3 py-1.5 text-sm hover:bg-accent transition-colors">
          {t('page.incident_detail.back_to_list')}
        </button>
      </div>

      {/* Header Card */}
      <Card>
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">{incident.title}</h2>
            <p className="mt-1 font-mono text-xs text-muted-foreground">{incident.id}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={severityVariant[incident.severity] || 'default'}>{t(`enum.incident_severity.${incident.severity}`)}</Badge>
            <Badge variant={statusVariant[incident.status] || 'default'}>{t(`enum.incident_status.${incident.status}`)}</Badge>
          </div>
        </div>
        {incident.description && (
          <div className="rounded-lg border border-border bg-secondary p-3 text-sm text-foreground whitespace-pre-wrap">
            {incident.description}
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* Left: Details + Timeline */}
        <div className="space-y-5 xl:col-span-2">
          {/* Overview */}
          <Card>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.overview')}</h3>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('table.type')}</p>
                <p className="mt-1 font-medium text-foreground">{t(`enum.incident_type.${incident.incident_type}`)}</p>
              </div>
              <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.reported_by')}</p>
                <p className="mt-1 text-foreground">{incident.reported_by_name || incident.reported_by}</p>
              </div>
              <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('table.assigned_to')}</p>
                <p className="mt-1 text-foreground">{incident.assigned_to_name || t('common.unassigned')}</p>
              </div>
              <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('table.detected_at')}</p>
                <p className="mt-1 text-foreground">{incident.detected_at ? formatDateTime(incident.detected_at) : '—'}</p>
              </div>
              {incident.attack_vector && (
                <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.attack_vector')}</p>
                  <p className="mt-1 text-foreground">{incident.attack_vector}</p>
                </div>
              )}
              {incident.data_breach_scope && (
                <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.data_breach_scope')}</p>
                  <p className="mt-1 text-foreground">{incident.data_breach_scope}</p>
                </div>
              )}
              {incident.close_reason && (
                <div className="rounded-lg border border-border bg-secondary px-3 py-2 sm:col-span-2">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.close_reason')}</p>
                  <p className="mt-1 text-foreground">{incident.close_reason}</p>
                </div>
              )}
              {incident.closed_at && (
                <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.closed_at')}</p>
                  <p className="mt-1 text-foreground">{formatDateTime(incident.closed_at)}</p>
                </div>
              )}
            </div>
          </Card>

          {/* NIS2 Regulatory Reports */}
          {incident.reports && incident.reports.length > 0 && (
            <Card>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.regulatory_reports')}</h3>
              <div className="space-y-3">
                {incident.reports.map((r) => (
                  <div key={r.id} className="rounded-lg border border-border bg-secondary px-4 py-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-foreground">
                          {t(`enum.report_type.${r.report_type}`, undefined, { defaultValue: REPORT_TYPE_LABELS[r.report_type] || r.report_type })}
                        </p>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {t('page.incident_detail.deadline')}: {r.deadline_at ? formatDateTime(r.deadline_at) : '—'}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={REPORT_STATUS_VARIANT[r.status] || 'default'}>
                          {t(`enum.report_status.${r.status}`, undefined, { defaultValue: r.status })}
                        </Badge>
                      </div>
                    </div>

                    {/* Countdown */}
                    {r.status !== 'submitted' && (
                      <div className="mt-2 flex items-center gap-3">
                        <CountdownTimer
                          initialSeconds={r.time_remaining_seconds ?? null}
                          elapsedPct={r.elapsed_percentage ?? null}
                        />
                        {r.elapsed_percentage != null && (
                          <div className="flex-1">
                            <div className="h-2 w-full rounded-full bg-muted">
                              <div
                                className={`h-2 rounded-full transition-all ${
                                  r.elapsed_percentage >= 100 ? 'bg-destructive' :
                                  r.elapsed_percentage >= 90 ? 'bg-red-500' :
                                  r.elapsed_percentage >= 75 ? 'bg-yellow-500' :
                                  'bg-green-500'
                                }`}
                                style={{ width: `${Math.min(r.elapsed_percentage, 100)}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Action buttons (admin only) */}
                    {isAdmin && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(r.status === 'pending' || r.status === 'generated') && (
                          <button
                            onClick={() => generateReport.mutate(r.id)}
                            disabled={generateReport.isPending}
                            className="inline-flex items-center gap-1.5 rounded-md border bg-background px-3 py-1.5 text-xs font-medium hover:bg-accent transition-colors disabled:opacity-50"
                          >
                            {r.status === 'generated' ? t('page.incident_detail.btn_regenerate') : t('page.incident_detail.btn_generate')}
                          </button>
                        )}
                        {r.status === 'generated' && (
                          <>
                            <button
                              onClick={() => { void downloadReport(r.id); }}
                              className="inline-flex items-center gap-1.5 rounded-md border bg-background px-3 py-1.5 text-xs font-medium hover:bg-accent transition-colors"
                            >
                              {t('page.incident_detail.btn_download')}
                            </button>
                            <button
                              onClick={() => submitReport.mutate(r.id)}
                              disabled={submitReport.isPending}
                              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
                            >
                              {t('page.incident_detail.btn_submit')}
                            </button>
                          </>
                        )}
                        {r.status === 'submitted' && r.generated_at && (
                          <button
                            onClick={() => { void downloadReport(r.id); }}
                            className="inline-flex items-center gap-1.5 rounded-md border bg-background px-3 py-1.5 text-xs font-medium hover:bg-accent transition-colors"
                          >
                            {t('page.incident_detail.btn_download')}
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Affected Assets */}
          <Card>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.affected_assets')}</h3>
            {incident.assets.length > 0 && (
              <div className="mb-3 space-y-2">
                {incident.assets.map((a) => (
                  <div key={a.asset_id} className="flex items-center justify-between rounded-lg border border-border bg-secondary px-3 py-2">
                    <div>
                      <p className="font-medium text-foreground">{a.asset_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {a.asset_type && <span className="capitalize">{t(`enum.asset_type.${a.asset_type}`, undefined, { defaultValue: a.asset_type })}</span>}
                        {a.impact_description && <span> — {a.impact_description}</span>}
                      </p>
                    </div>
                    {!isClosed && (
                      <button
                        onClick={() => unlinkAsset.mutate(a.asset_id)}
                        disabled={unlinkAsset.isPending}
                        className="text-xs text-destructive hover:underline disabled:opacity-50"
                      >
                        {t('common.remove')}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
            {!isClosed && (
              <div className="flex flex-col gap-2 sm:flex-row">
                <select
                  value={selectedAssetId}
                  onChange={(e) => setSelectedAssetId(e.target.value)}
                  className="flex-1"
                >
                  <option value="">{t('page.incident_detail.select_asset')}</option>
                  {allAssets
                    .filter((a) => !incident.assets.some((la) => la.asset_id === a.id))
                    .map((a) => (
                      <option key={a.id} value={a.id}>{a.brand} {a.model} ({a.serial_number})</option>
                    ))}
                </select>
                <input
                  type="text"
                  value={assetImpact}
                  onChange={(e) => setAssetImpact(e.target.value)}
                  placeholder={t('page.incident_detail.impact_placeholder')}
                  className="flex-1"
                />
                <button
                  onClick={() => {
                    if (selectedAssetId) linkAsset.mutate({ asset_id: selectedAssetId, impact_description: assetImpact || undefined });
                  }}
                  disabled={!selectedAssetId || linkAsset.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {linkAsset.isPending ? t('common.working') : t('common.add')}
                </button>
              </div>
            )}
            {incident.assets.length === 0 && isClosed && (
              <p className="text-sm text-muted-foreground">{t('page.incident_detail.no_assets')}</p>
            )}
          </Card>

          {/* Involved Vendors */}
          <Card>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.involved_vendors')}</h3>
            {incident.vendors.length > 0 && (
              <div className="mb-3 space-y-2">
                {incident.vendors.map((v) => (
                  <div key={v.vendor_id} className="flex items-center justify-between rounded-lg border border-border bg-secondary px-3 py-2">
                    <div>
                      <p className="font-medium text-foreground">{v.vendor_name}</p>
                      {v.involvement_description && (
                        <p className="text-xs text-muted-foreground">{v.involvement_description}</p>
                      )}
                    </div>
                    {!isClosed && (
                      <button
                        onClick={() => unlinkVendor.mutate(v.vendor_id)}
                        disabled={unlinkVendor.isPending}
                        className="text-xs text-destructive hover:underline disabled:opacity-50"
                      >
                        {t('common.remove')}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
            {!isClosed && (
              <div className="flex flex-col gap-2 sm:flex-row">
                <select
                  value={selectedVendorId}
                  onChange={(e) => setSelectedVendorId(e.target.value)}
                  className="flex-1"
                >
                  <option value="">{t('page.incident_detail.select_vendor')}</option>
                  {allVendors
                    .filter((v) => v.is_active && !incident.vendors.some((lv) => lv.vendor_id === v.id))
                    .map((v) => (
                      <option key={v.id} value={v.id}>{v.name}</option>
                    ))}
                </select>
                <input
                  type="text"
                  value={vendorInvolvement}
                  onChange={(e) => setVendorInvolvement(e.target.value)}
                  placeholder={t('page.incident_detail.involvement_placeholder')}
                  className="flex-1"
                />
                <button
                  onClick={() => {
                    if (selectedVendorId) linkVendor.mutate({ vendor_id: selectedVendorId, involvement_description: vendorInvolvement || undefined });
                  }}
                  disabled={!selectedVendorId || linkVendor.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {linkVendor.isPending ? t('common.working') : t('common.add')}
                </button>
              </div>
            )}
            {incident.vendors.length === 0 && isClosed && (
              <p className="text-sm text-muted-foreground">{t('page.incident_detail.no_vendors')}</p>
            )}
          </Card>

          {/* Post-Mortem */}
          {isRecoveredOrClosed && (
            <Card>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.postmortem')}</h3>
              {incident.postmortem && !pmEditing ? (
                <div className="space-y-3">
                  <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.pm_root_cause')}</p>
                    <p className="mt-1 text-sm text-foreground whitespace-pre-wrap">{incident.postmortem.root_cause}</p>
                  </div>
                  <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.pm_lessons_learned')}</p>
                    <p className="mt-1 text-sm text-foreground whitespace-pre-wrap">{incident.postmortem.lessons_learned}</p>
                  </div>
                  <div className="rounded-lg border border-border bg-secondary px-3 py-2">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.pm_corrective_actions')}</p>
                    <p className="mt-1 text-sm text-foreground whitespace-pre-wrap">{incident.postmortem.corrective_actions}</p>
                  </div>
                  {incident.postmortem.created_by_name && (
                    <p className="text-xs text-muted-foreground">
                      {t('page.incident_detail.pm_created_by')}: {incident.postmortem.created_by_name}
                      {incident.postmortem.created_at && ` — ${formatDateTime(incident.postmortem.created_at)}`}
                    </p>
                  )}
                  {isAdmin && (
                    <button
                      onClick={() => {
                        setPmRootCause(incident.postmortem!.root_cause);
                        setPmLessons(incident.postmortem!.lessons_learned);
                        setPmActions(incident.postmortem!.corrective_actions);
                        setPmEditing(true);
                      }}
                      className="inline-flex items-center gap-1.5 rounded-md border bg-background px-3 py-1.5 text-xs font-medium hover:bg-accent transition-colors"
                    >
                      {t('common.edit')}
                    </button>
                  )}
                </div>
              ) : isAdmin ? (
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">{t('page.incident_detail.pm_root_cause')}</label>
                    <textarea
                      value={pmRootCause}
                      onChange={(e) => setPmRootCause(e.target.value)}
                      rows={3}
                      className="mt-1 w-full"
                      placeholder={t('page.incident_detail.pm_root_cause_placeholder')}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">{t('page.incident_detail.pm_lessons_learned')}</label>
                    <textarea
                      value={pmLessons}
                      onChange={(e) => setPmLessons(e.target.value)}
                      rows={3}
                      className="mt-1 w-full"
                      placeholder={t('page.incident_detail.pm_lessons_placeholder')}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">{t('page.incident_detail.pm_corrective_actions')}</label>
                    <textarea
                      value={pmActions}
                      onChange={(e) => setPmActions(e.target.value)}
                      rows={3}
                      className="mt-1 w-full"
                      placeholder={t('page.incident_detail.pm_actions_placeholder')}
                    />
                  </div>
                  <div className="flex gap-2">
                    {pmEditing && (
                      <button
                        onClick={() => { setPmEditing(false); setPmRootCause(''); setPmLessons(''); setPmActions(''); }}
                        className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent transition-all"
                      >
                        {t('common.cancel')}
                      </button>
                    )}
                    <button
                      onClick={() => {
                        if (pmEditing) {
                          updatePostMortem.mutate({ root_cause: pmRootCause, lessons_learned: pmLessons, corrective_actions: pmActions });
                        } else {
                          createPostMortem.mutate({ root_cause: pmRootCause, lessons_learned: pmLessons, corrective_actions: pmActions });
                        }
                      }}
                      disabled={!pmRootCause.trim() || !pmLessons.trim() || !pmActions.trim() || createPostMortem.isPending || updatePostMortem.isPending}
                      className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                    >
                      {(createPostMortem.isPending || updatePostMortem.isPending) ? t('common.working') : t('common.save')}
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">{t('page.incident_detail.no_postmortem')}</p>
              )}
            </Card>
          )}

          {/* Timeline */}
          <Card>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.timeline')}</h3>
            {incident.timeline.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t('page.incident_detail.no_timeline')}</p>
            ) : (
              <div className="space-y-3">
                {incident.timeline.map((entry) => (
                  <div key={entry.id} className="rounded-lg border border-border bg-secondary px-3 py-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="default">{t(`enum.timeline_event.${entry.event_type}`, undefined, { defaultValue: entry.event_type })}</Badge>
                      <span className="text-xs text-muted-foreground">{entry.created_at ? formatDateTime(entry.created_at) : ''}</span>
                    </div>
                    <p className="mt-1.5 text-sm text-foreground">{entry.description}</p>
                    {entry.actor_name && (
                      <p className="mt-1 text-xs text-muted-foreground">{entry.actor_name}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right: Actions */}
        <div className="space-y-5">
          {/* Status transitions */}
          {!isClosed && nextStatuses.length > 0 && (
            <Card>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.change_status')}</h3>
              <div className="flex flex-wrap gap-2">
                {nextStatuses.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleStatusChange(s)}
                    disabled={changeStatus.isPending}
                    className={`inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium shadow-xs transition-all disabled:opacity-50 ${
                      s === 'closed'
                        ? 'bg-destructive text-white hover:bg-destructive/90'
                        : 'bg-primary text-primary-foreground hover:bg-primary/90'
                    }`}
                  >
                    {changeStatus.isPending ? t('common.working') : t(`enum.incident_status.${s}`)}
                  </button>
                ))}
              </div>
            </Card>
          )}

          {/* Severity change */}
          {!isClosed && (
            <Card>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.change_severity')}</h3>
              <div className="flex gap-2">
                <select
                  value={newSeverity}
                  onChange={(e) => setNewSeverity(e.target.value)}
                  className="w-full"
                >
                  <option value="">{t('page.incident_detail.select_severity')}</option>
                  {['P1', 'P2', 'P3', 'P4'].filter((s) => s !== incident.severity).map((s) => (
                    <option key={s} value={s}>{t(`enum.incident_severity.${s}`)}</option>
                  ))}
                </select>
                <button
                  onClick={() => { if (newSeverity) changeSeverity.mutate(newSeverity); }}
                  disabled={!newSeverity || changeSeverity.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {changeSeverity.isPending ? t('common.working') : t('common.save')}
                </button>
              </div>
            </Card>
          )}

          {/* Assignment */}
          {!isClosed && (
            <Card>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t('page.incident_detail.assign')}</h3>
              <div className="flex gap-2">
                <select
                  value={assignUserId}
                  onChange={(e) => setAssignUserId(e.target.value)}
                  className="w-full"
                >
                  <option value="">{t('page.incident_detail.select_technician')}</option>
                  {technicians.filter((tech) => tech.is_active).map((tech) => (
                    <option key={tech.id} value={tech.id}>{tech.name || tech.email}</option>
                  ))}
                </select>
                <button
                  onClick={() => { if (assignUserId) assignIncident.mutate(assignUserId); }}
                  disabled={!assignUserId || assignIncident.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {assignIncident.isPending ? t('common.working') : t('page.incident_detail.assign')}
                </button>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Close reason modal */}
      {closeModalOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => { if (!changeStatus.isPending) setCloseModalOpen(false); }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.incident_detail.close_incident')}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{t('page.incident_detail.close_reason_required')}</p>

            <div className="mt-4 space-y-3">
              <textarea
                value={closeReason}
                onChange={(e) => setCloseReason(e.target.value)}
                placeholder={t('page.incident_detail.close_reason_placeholder')}
                rows={3}
                className="w-full"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setCloseModalOpen(false)}
                  disabled={changeStatus.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (!closeReason.trim()) {
                      showToast({ title: t('page.incident_detail.close_reason_required'), variant: 'error' });
                      return;
                    }
                    changeStatus.mutate({ status: 'closed', close_reason: closeReason });
                  }}
                  disabled={changeStatus.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50"
                >
                  {changeStatus.isPending ? t('common.working') : t('page.incident_detail.close_incident')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
