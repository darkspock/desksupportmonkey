import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { formatDateTime, formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../hooks/useToast';
import { Pencil } from 'lucide-react';
import type { ChangeRequestDetail, ChangeAsset, PIR } from '../../types';

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

const eventIcon: Record<string, string> = {
  created: '📝',
  updated: '✏️',
  submitted: '📤',
  approved: '✅',
  rejected: '❌',
  started: '▶️',
  implemented: '🚀',
  rolled_back: '⏪',
  closed: '🔒',
  assigned: '👤',
  asset_linked: '🔗',
  asset_unlinked: '🔗',
  pir_added: '📋',
};

const eventColor: Record<string, string> = {
  created: 'border-l-muted-foreground',
  updated: 'border-l-muted-foreground',
  submitted: 'border-l-blue-500',
  approved: 'border-l-green-500',
  rejected: 'border-l-red-500',
  started: 'border-l-blue-500',
  implemented: 'border-l-blue-500',
  rolled_back: 'border-l-red-500',
  closed: 'border-l-green-500',
  assigned: 'border-l-muted-foreground',
  asset_linked: 'border-l-blue-500',
  asset_unlinked: 'border-l-muted-foreground',
};

const TERMINAL_STATUSES = ['closed', 'rejected', 'rolled_back'];
const UNLINKABLE_STATUSES = ['draft', 'pending_approval', 'scheduled'];

export default function ChangeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  const [showApprove, setShowApprove] = useState(false);
  const [approveNotes, setApproveNotes] = useState('');
  const [showReject, setShowReject] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [showImplement, setShowImplement] = useState(false);
  const [implementNotes, setImplementNotes] = useState('');
  const [showRollback, setShowRollback] = useState(false);
  const [rollbackReason, setRollbackReason] = useState('');
  const [showAssign, setShowAssign] = useState(false);
  const [assignTo, setAssignTo] = useState('');
  const [showLinkAssets, setShowLinkAssets] = useState(false);
  const [assetSearch, setAssetSearch] = useState('');
  const [selectedAssetIds, setSelectedAssetIds] = useState<string[]>([]);
  const [unlinkTarget, setUnlinkTarget] = useState<ChangeAsset | null>(null);
  const [showCreatePIR, setShowCreatePIR] = useState(false);
  const [pirForm, setPirForm] = useState({ outcome: '', issues_found: '', lessons_learned: '', follow_up_actions: '' });
  const [showEdit, setShowEdit] = useState(false);
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    change_type: '',
    business_justification: '',
    risk_assessment: '',
    rollback_plan: '',
    planned_date: '',
  });

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['change', id],
    queryFn: async () => {
      const { data } = await api.get(`/changes/${id}`);
      return data as ChangeRequestDetail;
    },
    enabled: !!id,
  });

  const actionMutation = (
    method: 'post' | 'patch',
    url: string,
    payload: Record<string, unknown> | undefined,
    successMsg: string,
    errorMsg: string,
    onDone?: () => void,
  ) =>
    useMutation({
      mutationFn: async () => {
        if (method === 'post') await api.post(url, payload || {});
        else await api.patch(url, payload || {});
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['change', id] });
        queryClient.invalidateQueries({ queryKey: ['changes'] });
        showToast({ title: successMsg, variant: 'success' });
        onDone?.();
      },
      onError: (err: unknown) => {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error';
        showToast({ title: errorMsg, description: detail, variant: 'error' });
      },
    });

  const submitMut = actionMutation('post', `/changes/${id}/submit`, undefined, t('page.change_detail.toast_submitted'), t('page.change_detail.error_action'));
  const startMut = actionMutation('post', `/changes/${id}/start`, undefined, t('page.change_detail.toast_started'), t('page.change_detail.error_action'));
  const closeMut = actionMutation('post', `/changes/${id}/close`, undefined, t('page.change_detail.toast_closed'), t('page.change_detail.error_action'));

  const approveMut = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {};
      if (approveNotes.trim()) payload.notes = approveNotes.trim();
      await api.post(`/changes/${id}/approve`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['change', id] });
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      setShowApprove(false);
      setApproveNotes('');
      showToast({ title: t('page.change_detail.toast_approved'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error';
      showToast({ title: t('page.change_detail.error_action'), description: detail, variant: 'error' });
    },
  });

  const rejectMut = useMutation({
    mutationFn: async () => {
      await api.post(`/changes/${id}/reject`, { reason: rejectReason.trim() });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['change', id] });
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      setShowReject(false);
      setRejectReason('');
      showToast({ title: t('page.change_detail.toast_rejected'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error';
      showToast({ title: t('page.change_detail.error_action'), description: detail, variant: 'error' });
    },
  });

  const implementMut = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {};
      if (implementNotes.trim()) payload.notes = implementNotes.trim();
      await api.post(`/changes/${id}/implement`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['change', id] });
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      setShowImplement(false);
      setImplementNotes('');
      showToast({ title: t('page.change_detail.toast_implemented'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error';
      showToast({ title: t('page.change_detail.error_action'), description: detail, variant: 'error' });
    },
  });

  const rollbackMut = useMutation({
    mutationFn: async () => {
      await api.post(`/changes/${id}/rollback`, { reason: rollbackReason.trim() });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['change', id] });
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      setShowRollback(false);
      setRollbackReason('');
      showToast({ title: t('page.change_detail.toast_rolled_back'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error';
      showToast({ title: t('page.change_detail.error_action'), description: detail, variant: 'error' });
    },
  });

  const assignMut = useMutation({
    mutationFn: async () => {
      await api.post(`/changes/${id}/assign`, { assigned_to: assignTo.trim() });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['change', id] });
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      setShowAssign(false);
      setAssignTo('');
      showToast({ title: t('page.change_detail.toast_assigned'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error';
      showToast({ title: t('page.change_detail.error_action'), description: detail, variant: 'error' });
    },
  });

  const editMut = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {};
      if (editForm.title.trim()) payload.title = editForm.title.trim();
      if (editForm.description !== undefined) payload.description = editForm.description;
      if (editForm.change_type) payload.change_type = editForm.change_type;
      if (editForm.business_justification !== undefined) payload.business_justification = editForm.business_justification;
      if (editForm.risk_assessment !== undefined) payload.risk_assessment = editForm.risk_assessment;
      if (editForm.rollback_plan !== undefined) payload.rollback_plan = editForm.rollback_plan;
      if (editForm.planned_date) payload.planned_date = editForm.planned_date;
      await api.patch(`/changes/${id}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['change', id] });
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      setShowEdit(false);
      showToast({ title: t('page.change_detail.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error';
      showToast({ title: t('page.change_detail.error_action'), description: detail, variant: 'error' });
    },
  });

  const assignableUsersQuery = useQuery({
    queryKey: ['assignable-users-changes'],
    queryFn: async () => {
      const [techRes, adminRes] = await Promise.all([
        api.get('/users', { params: { role: 'technician', page_size: 100, is_active: true } }),
        api.get('/users', { params: { role: 'admin', page_size: 100, is_active: true } }),
      ]);
      const all = [...(techRes.data.data || []), ...(adminRes.data.data || [])];
      const seen = new Set<string>();
      return all.filter((u: { id: string }) => {
        if (seen.has(u.id)) return false;
        seen.add(u.id);
        return true;
      }) as Array<{ id: string; first_name: string; last_name: string; email: string; role: string }>;
    },
    enabled: showAssign,
  });

  const assetSearchQuery = useQuery({
    queryKey: ['assets-search', assetSearch],
    queryFn: async () => {
      const { data } = await api.get(`/assets`, { params: { search: assetSearch, page_size: 20 } });
      return data.data as Array<{ id: string; brand: string; model: string; serial_number: string }>;
    },
    enabled: showLinkAssets && assetSearch.length >= 2,
  });

  const linkAssetsMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/changes/${id}/assets`, { asset_ids: selectedAssetIds });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['change', id] });
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      setShowLinkAssets(false);
      setSelectedAssetIds([]);
      setAssetSearch('');
      showToast({ title: t('page.change_detail.toast_assets_linked'), variant: 'success' });
    },
    onError: () => {
      showToast({ title: t('page.change_detail.error_link'), variant: 'error' });
    },
  });

  const unlinkMutation = useMutation({
    mutationFn: async (assetId: string) => {
      await api.delete(`/changes/${id}/assets/${assetId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['change', id] });
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      setUnlinkTarget(null);
      showToast({ title: t('page.change_detail.toast_asset_unlinked'), variant: 'success' });
    },
    onError: () => {
      showToast({ title: t('page.change_detail.error_unlink'), variant: 'error' });
    },
  });

  const createPIRMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = { outcome: pirForm.outcome };
      if (pirForm.issues_found.trim()) payload.issues_found = pirForm.issues_found.trim();
      if (pirForm.lessons_learned.trim()) payload.lessons_learned = pirForm.lessons_learned.trim();
      if (pirForm.follow_up_actions.trim()) payload.follow_up_actions = pirForm.follow_up_actions.trim();
      await api.post(`/changes/${id}/pir`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['change', id] });
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      setShowCreatePIR(false);
      setPirForm({ outcome: '', issues_found: '', lessons_learned: '', follow_up_actions: '' });
      showToast({ title: t('page.change_detail.toast_pir_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error';
      showToast({ title: t('page.change_detail.error_pir_create'), description: detail, variant: 'error' });
    },
  });

  const openEdit = () => {
    if (!data) return;
    setEditForm({
      title: data.title,
      description: data.description || '',
      change_type: data.change_type,
      business_justification: data.business_justification || '',
      risk_assessment: data.risk_assessment || '',
      rollback_plan: data.rollback_plan || '',
      planned_date: data.planned_date ? data.planned_date.slice(0, 16) : '',
    });
    setShowEdit(true);
  };

  const isTerminal = data ? TERMINAL_STATUSES.includes(data.status) : false;
  const isEditable = data ? ['draft', 'pending_approval'].includes(data.status) : false;
  const inputClasses = 'w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring';

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error).message} onRetry={refetch} />;
  if (!data) return null;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link to="/changes" className="text-sm text-muted-foreground hover:text-foreground">
            &larr; {t('page.changes.title')}
          </Link>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight text-foreground">{data.title}</h2>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant={statusVariant[data.status] || 'default'}>
              {t(`enum.change_status.${data.status}`)}
            </Badge>
            <Badge variant={typeVariant[data.change_type] || 'default'}>
              {t(`enum.change_type.${data.change_type}`)}
            </Badge>
          </div>
        </div>
        {!isTerminal && (
          <div className="flex flex-wrap gap-2">
            {data.status === 'draft' && (
              <button onClick={() => submitMut.mutate()} disabled={submitMut.isPending} className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50">{t('page.change_detail.btn_submit')}</button>
            )}
            {data.status === 'pending_approval' && (
              <>
                {isAdmin && <button onClick={() => setShowApprove(true)} className="h-9 rounded-md bg-green-600 px-4 text-sm font-medium text-white shadow-xs hover:bg-green-700">{t('page.change_detail.btn_approve')}</button>}
                {isAdmin && <button onClick={() => setShowReject(true)} className="h-9 rounded-md bg-red-600 px-4 text-sm font-medium text-white shadow-xs hover:bg-red-700">{t('page.change_detail.btn_reject')}</button>}
              </>
            )}
            {data.status === 'scheduled' && (
              <button onClick={() => startMut.mutate()} disabled={startMut.isPending} className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50">{t('page.change_detail.btn_start')}</button>
            )}
            {data.status === 'in_progress' && (
              <>
                <button onClick={() => setShowImplement(true)} className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90">{t('page.change_detail.btn_implement')}</button>
                <button onClick={() => setShowRollback(true)} className="h-9 rounded-md bg-red-600 px-4 text-sm font-medium text-white shadow-xs hover:bg-red-700">{t('page.change_detail.btn_rollback')}</button>
              </>
            )}
            {data.status === 'implemented' && (
              <>
                {isAdmin && <button onClick={() => closeMut.mutate()} disabled={closeMut.isPending} className="h-9 rounded-md bg-green-600 px-4 text-sm font-medium text-white shadow-xs hover:bg-green-700 disabled:opacity-50">{t('page.change_detail.btn_close')}</button>}
                <button onClick={() => setShowRollback(true)} className="h-9 rounded-md bg-red-600 px-4 text-sm font-medium text-white shadow-xs hover:bg-red-700">{t('page.change_detail.btn_rollback')}</button>
              </>
            )}
            {isAdmin && <button onClick={() => setShowAssign(true)} className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50">{t('page.change_detail.btn_assign')}</button>}
          </div>
        )}
      </div>

      {/* Details Card */}
      <Card>
        <div className="grid grid-cols-1 gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.requested_by')}</p>
            <p className="mt-1 text-sm">{data.requested_by_name || data.requested_by}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.assigned_to')}</p>
            <p className="mt-1 text-sm">{data.assigned_to_name || data.assigned_to || '—'}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.planned_date')}</p>
            <p className="mt-1 text-sm">{data.planned_date ? formatDate(data.planned_date) : '—'}</p>
          </div>
          {data.approved_by && (
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.approved_by')}</p>
              <p className="mt-1 text-sm">{data.approved_by_name || data.approved_by}{data.approved_at ? ` · ${formatDateTime(data.approved_at)}` : ''}</p>
            </div>
          )}
          {data.rejected_by && (
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.rejected_by')}</p>
              <p className="mt-1 text-sm">{data.rejected_by_name || data.rejected_by}{data.rejected_at ? ` · ${formatDateTime(data.rejected_at)}` : ''}</p>
            </div>
          )}
          {data.started_at && (
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.started_at')}</p>
              <p className="mt-1 text-sm">{formatDateTime(data.started_at)}</p>
            </div>
          )}
          {data.implemented_at && (
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.implemented_at')}</p>
              <p className="mt-1 text-sm">{formatDateTime(data.implemented_at)}</p>
            </div>
          )}
          {data.closed_at && (
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.closed_at')}</p>
              <p className="mt-1 text-sm">{formatDateTime(data.closed_at)}</p>
            </div>
          )}
          <div>
            <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.created_at')}</p>
            <p className="mt-1 text-sm">{data.created_at ? formatDateTime(data.created_at) : '—'}</p>
          </div>
        </div>
        {data.rejection_reason && (
          <div className="border-t border-border p-4">
            <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.rejection_reason')}</p>
            <p className="mt-1 text-sm whitespace-pre-wrap text-destructive">{data.rejection_reason}</p>
          </div>
        )}
        {data.rollback_reason && (
          <div className="border-t border-border p-4">
            <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.rollback_reason')}</p>
            <p className="mt-1 text-sm whitespace-pre-wrap text-destructive">{data.rollback_reason}</p>
          </div>
        )}
      </Card>

      {/* Content Card — Description, Justification, Risk, Rollback, Notes */}
      <Card>
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-foreground">{t('page.change_detail.section_details')}</h3>
            {isEditable && (
              <button
                onClick={openEdit}
                className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors"
                title={t('page.change_detail.btn_edit')}
              >
                <Pencil className="h-4 w-4" />
              </button>
            )}
          </div>
          <div className="flex flex-col gap-4">
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.description')}</p>
              <p className="mt-1 text-sm whitespace-pre-wrap">{data.description || '—'}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.business_justification')}</p>
              <p className="mt-1 text-sm whitespace-pre-wrap">{data.business_justification || '—'}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.risk_assessment')}</p>
              <p className="mt-1 text-sm whitespace-pre-wrap">{data.risk_assessment || '—'}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.rollback_plan')}</p>
              <p className="mt-1 text-sm whitespace-pre-wrap">{data.rollback_plan || '—'}</p>
            </div>
            {data.implementation_notes && (
              <div>
                <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.implementation_notes')}</p>
                <p className="mt-1 text-sm whitespace-pre-wrap">{data.implementation_notes}</p>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Affected Assets */}
      <Card>
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-foreground">
              {t('page.change_detail.affected_assets')}
              {data.affected_assets && data.affected_assets.length > 0 && (
                <span className="ml-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-muted px-1.5 text-xs font-medium">
                  {data.affected_assets.length}
                </span>
              )}
            </h3>
            {!isTerminal && (
              <button
                onClick={() => setShowLinkAssets(true)}
                className="h-8 rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground shadow-xs hover:bg-primary/90"
              >
                {t('page.change_detail.link_assets')}
              </button>
            )}
          </div>
          {!data.affected_assets || data.affected_assets.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t('page.change_detail.no_assets_linked')}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    <th className="pb-2 pr-4 text-xs font-medium uppercase text-muted-foreground">Asset</th>
                    <th className="pb-2 pr-4 text-xs font-medium uppercase text-muted-foreground">Serial / Tag</th>
                    <th className="pb-2 pr-4 text-xs font-medium uppercase text-muted-foreground">Brand</th>
                    <th className="pb-2 pr-4 text-xs font-medium uppercase text-muted-foreground">Model</th>
                    <th className="pb-2 text-xs font-medium uppercase text-muted-foreground"></th>
                  </tr>
                </thead>
                <tbody>
                  {data.affected_assets.map((ca) => (
                    <tr key={ca.id} className="border-b border-border/50 last:border-0">
                      <td className="py-2 pr-4 font-medium">{ca.asset_name || ca.asset_id}</td>
                      <td className="py-2 pr-4 font-mono text-xs">{ca.asset_tag || '—'}</td>
                      <td className="py-2 pr-4">{ca.asset_brand || '—'}</td>
                      <td className="py-2 pr-4">{ca.asset_model || '—'}</td>
                      <td className="py-2">
                        {UNLINKABLE_STATUSES.includes(data.status) && (
                          <button
                            onClick={() => setUnlinkTarget(ca)}
                            className="text-xs text-destructive hover:text-destructive/80"
                          >
                            &times;
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>

      {/* Post-Implementation Review */}
      {(data.pir || data.status === 'implemented') && (
        <Card>
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-foreground">{t('page.change_detail.pir_section')}</h3>
              {!data.pir && data.status === 'implemented' && isAdmin && (
                <button
                  onClick={() => setShowCreatePIR(true)}
                  className="h-8 rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground shadow-xs hover:bg-primary/90"
                >
                  {t('page.change_detail.pir_add_review')}
                </button>
              )}
            </div>
            {data.pir ? (
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.pir_outcome')}:</span>
                  <Badge variant={data.pir.outcome === 'successful' ? 'success' : data.pir.outcome === 'partial' ? 'warning' : 'danger'}>
                    {t(`page.change_detail.pir_outcome_${data.pir.outcome}`)}
                  </Badge>
                </div>
                {data.pir.issues_found && (
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.pir_issues_found')}</p>
                    <p className="mt-1 text-sm whitespace-pre-wrap">{data.pir.issues_found}</p>
                  </div>
                )}
                {data.pir.lessons_learned && (
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.pir_lessons_learned')}</p>
                    <p className="mt-1 text-sm whitespace-pre-wrap">{data.pir.lessons_learned}</p>
                  </div>
                )}
                {data.pir.follow_up_actions && (
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">{t('page.change_detail.pir_follow_up_actions')}</p>
                    <p className="mt-1 text-sm whitespace-pre-wrap">{data.pir.follow_up_actions}</p>
                  </div>
                )}
                <div className="text-xs text-muted-foreground">
                  {data.pir.created_by_name || data.pir.created_by}
                  {data.pir.created_at && ` · ${formatDateTime(data.pir.created_at)}`}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{t('page.change_detail.pir_add_review')}</p>
            )}
          </div>
        </Card>
      )}

      {/* Timeline */}
      {data.timeline && data.timeline.length > 0 && (
        <Card>
          <div className="p-4">
            <h3 className="text-sm font-semibold text-foreground mb-4">{t('page.change_detail.timeline')}</h3>
            <div className="relative flex flex-col gap-0">
              {data.timeline.map((event, idx) => (
                <div key={event.id} className="relative flex gap-3">
                  {/* Connector line */}
                  {idx < data.timeline.length - 1 && (
                    <div className="absolute left-4 top-8 bottom-0 w-px bg-border" />
                  )}
                  {/* Icon */}
                  <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-sm">
                    {eventIcon[event.event_type] || '•'}
                  </div>
                  {/* Content */}
                  <div className={`flex-1 mb-4 rounded-md border-l-4 ${eventColor[event.event_type] || 'border-l-border'} bg-muted/30 p-3`}>
                    <p className="text-sm font-medium">
                      {t(`page.change_detail.event_${event.event_type}`)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {event.actor_name || event.actor_id}
                      {event.created_at && ` · ${formatDateTime(event.created_at)}`}
                    </p>
                    {event.description && (
                      <p className="mt-1 text-xs text-muted-foreground">{event.description}</p>
                    )}
                    {event.metadata && Object.keys(event.metadata).length > 0 && (
                      <div className="mt-1 text-xs text-muted-foreground">
                        {event.metadata.notes && <span className="italic">&quot;{String(event.metadata.notes)}&quot;</span>}
                        {event.metadata.reason && <span className="italic">&quot;{String(event.metadata.reason)}&quot;</span>}
                        {event.metadata.auto_approved !== undefined && (
                          <span>{event.metadata.auto_approved ? t('page.change_detail.auto_approved') : ''}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Approve Modal */}
      {showApprove && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold">{t('page.change_detail.btn_approve')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); approveMut.mutate(); }} className="flex flex-col gap-3">
              <textarea placeholder={t('page.change_detail.approve_notes_placeholder')} value={approveNotes} onChange={(e) => setApproveNotes(e.target.value)} className={inputClasses} rows={3} />
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => { setShowApprove(false); setApproveNotes(''); }} className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50">{t('common.cancel')}</button>
                <button type="submit" disabled={approveMut.isPending} className="h-9 rounded-md bg-green-600 px-4 text-sm font-medium text-white shadow-xs hover:bg-green-700 disabled:opacity-50">{approveMut.isPending ? t('common.saving') : t('page.change_detail.btn_approve')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showReject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold">{t('page.change_detail.btn_reject')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); rejectMut.mutate(); }} className="flex flex-col gap-3">
              <textarea placeholder={t('page.change_detail.reject_reason_placeholder') + ' *'} value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} className={inputClasses} rows={3} required />
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => { setShowReject(false); setRejectReason(''); }} className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50">{t('common.cancel')}</button>
                <button type="submit" disabled={!rejectReason.trim() || rejectMut.isPending} className="h-9 rounded-md bg-red-600 px-4 text-sm font-medium text-white shadow-xs hover:bg-red-700 disabled:opacity-50">{rejectMut.isPending ? t('common.saving') : t('page.change_detail.btn_reject')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Implement Modal */}
      {showImplement && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold">{t('page.change_detail.btn_implement')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); implementMut.mutate(); }} className="flex flex-col gap-3">
              <textarea placeholder={t('page.change_detail.implement_notes_placeholder')} value={implementNotes} onChange={(e) => setImplementNotes(e.target.value)} className={inputClasses} rows={3} />
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => { setShowImplement(false); setImplementNotes(''); }} className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50">{t('common.cancel')}</button>
                <button type="submit" disabled={implementMut.isPending} className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50">{implementMut.isPending ? t('common.saving') : t('page.change_detail.btn_implement')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Rollback Modal */}
      {showRollback && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold">{t('page.change_detail.btn_rollback')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); rollbackMut.mutate(); }} className="flex flex-col gap-3">
              <textarea placeholder={t('page.change_detail.rollback_reason_placeholder') + ' *'} value={rollbackReason} onChange={(e) => setRollbackReason(e.target.value)} className={inputClasses} rows={3} required />
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => { setShowRollback(false); setRollbackReason(''); }} className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50">{t('common.cancel')}</button>
                <button type="submit" disabled={!rollbackReason.trim() || rollbackMut.isPending} className="h-9 rounded-md bg-red-600 px-4 text-sm font-medium text-white shadow-xs hover:bg-red-700 disabled:opacity-50">{rollbackMut.isPending ? t('common.saving') : t('page.change_detail.btn_rollback')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Modal */}
      {showAssign && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold">{t('page.change_detail.btn_assign')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); assignMut.mutate(); }} className="flex flex-col gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.assigned_to')} *</label>
                <select value={assignTo} onChange={(e) => setAssignTo(e.target.value)} className={inputClasses} required>
                  <option value="">{t('page.change_detail.assign_select_user')}</option>
                  {assignableUsersQuery.data?.map((u) => (
                    <option key={u.id} value={u.id}>{u.first_name} {u.last_name} ({u.role})</option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => { setShowAssign(false); setAssignTo(''); }} className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50">{t('common.cancel')}</button>
                <button type="submit" disabled={!assignTo.trim() || assignMut.isPending} className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50">{assignMut.isPending ? t('common.saving') : t('page.change_detail.btn_assign')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEdit && isEditable && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="mb-4 text-lg font-semibold">{t('page.change_detail.btn_edit')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); editMut.mutate(); }} className="flex flex-col gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.changes.field_title')} *</label>
                <input value={editForm.title} onChange={(e) => setEditForm({ ...editForm, title: e.target.value })} className={inputClasses} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.description')}</label>
                <textarea value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} className={inputClasses} rows={3} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.change_type')}</label>
                <select value={editForm.change_type} onChange={(e) => setEditForm({ ...editForm, change_type: e.target.value })} className={inputClasses}>
                  <option value="standard">{t('enum.change_type.standard')}</option>
                  <option value="normal">{t('enum.change_type.normal')}</option>
                  <option value="emergency">{t('enum.change_type.emergency')}</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.business_justification')}</label>
                <textarea value={editForm.business_justification} onChange={(e) => setEditForm({ ...editForm, business_justification: e.target.value })} className={inputClasses} rows={2} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.risk_assessment')}</label>
                <textarea value={editForm.risk_assessment} onChange={(e) => setEditForm({ ...editForm, risk_assessment: e.target.value })} className={inputClasses} rows={2} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.rollback_plan')}</label>
                <textarea value={editForm.rollback_plan} onChange={(e) => setEditForm({ ...editForm, rollback_plan: e.target.value })} className={inputClasses} rows={2} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.changes.field_planned_date')}</label>
                <input type="datetime-local" value={editForm.planned_date} onChange={(e) => setEditForm({ ...editForm, planned_date: e.target.value })} className={inputClasses} />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setShowEdit(false)} className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50">{t('common.cancel')}</button>
                <button type="submit" disabled={editMut.isPending} className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50">{editMut.isPending ? t('common.saving') : t('common.save')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Link Assets Modal */}
      {showLinkAssets && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold">{t('page.change_detail.link_assets_title')}</h3>
            <input
              placeholder={t('page.change_detail.search_assets')}
              value={assetSearch}
              onChange={(e) => setAssetSearch(e.target.value)}
              className={inputClasses}
            />
            <div className="mt-3 max-h-60 overflow-y-auto border border-border rounded-md">
              {assetSearchQuery.data?.map((asset) => {
                const checked = selectedAssetIds.includes(asset.id);
                return (
                  <label key={asset.id} className="flex items-center gap-3 px-3 py-2 hover:bg-muted/50 cursor-pointer border-b border-border/50 last:border-0">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => {
                        setSelectedAssetIds(prev =>
                          checked ? prev.filter(i => i !== asset.id) : [...prev, asset.id]
                        );
                      }}
                      className="h-4 w-4 rounded border-border"
                    />
                    <span className="text-sm">{asset.brand} {asset.model}</span>
                    <span className="ml-auto font-mono text-xs text-muted-foreground">{asset.serial_number}</span>
                  </label>
                );
              })}
              {assetSearch.length >= 2 && assetSearchQuery.data?.length === 0 && (
                <p className="p-3 text-sm text-muted-foreground">No assets found.</p>
              )}
              {assetSearch.length < 2 && (
                <p className="p-3 text-sm text-muted-foreground">Type at least 2 characters to search.</p>
              )}
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => { setShowLinkAssets(false); setSelectedAssetIds([]); setAssetSearch(''); }}
                className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={() => linkAssetsMutation.mutate()}
                disabled={selectedAssetIds.length === 0 || linkAssetsMutation.isPending}
                className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
              >
                {linkAssetsMutation.isPending ? t('common.saving') : t('page.change_detail.link_assets')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create PIR Modal */}
      {showCreatePIR && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold">{t('page.change_detail.pir_create_title')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); createPIRMutation.mutate(); }} className="flex flex-col gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.pir_outcome')} *</label>
                <select value={pirForm.outcome} onChange={(e) => setPirForm({ ...pirForm, outcome: e.target.value })} className={inputClasses} required>
                  <option value="">{t('page.change_detail.pir_select_outcome')}</option>
                  <option value="successful">{t('page.change_detail.pir_outcome_successful')}</option>
                  <option value="partial">{t('page.change_detail.pir_outcome_partial')}</option>
                  <option value="failed">{t('page.change_detail.pir_outcome_failed')}</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.pir_issues_found')}</label>
                <textarea value={pirForm.issues_found} onChange={(e) => setPirForm({ ...pirForm, issues_found: e.target.value })} className={inputClasses} rows={2} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.pir_lessons_learned')}</label>
                <textarea value={pirForm.lessons_learned} onChange={(e) => setPirForm({ ...pirForm, lessons_learned: e.target.value })} className={inputClasses} rows={2} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">{t('page.change_detail.pir_follow_up_actions')}</label>
                <textarea value={pirForm.follow_up_actions} onChange={(e) => setPirForm({ ...pirForm, follow_up_actions: e.target.value })} className={inputClasses} rows={2} />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => { setShowCreatePIR(false); setPirForm({ outcome: '', issues_found: '', lessons_learned: '', follow_up_actions: '' }); }} className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50">{t('common.cancel')}</button>
                <button type="submit" disabled={!pirForm.outcome || createPIRMutation.isPending} className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50">{createPIRMutation.isPending ? t('common.saving') : t('common.save')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Unlink Confirmation Modal */}
      {unlinkTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-3 text-lg font-semibold">{t('page.change_detail.unlink_asset')}</h3>
            <p className="text-sm text-muted-foreground">{t('page.change_detail.confirm_unlink')}</p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setUnlinkTarget(null)}
                className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={() => unlinkMutation.mutate(unlinkTarget.asset_id)}
                disabled={unlinkMutation.isPending}
                className="h-9 rounded-md bg-destructive px-4 text-sm font-medium text-destructive-foreground shadow-xs hover:bg-destructive/90 disabled:opacity-50"
              >
                {unlinkMutation.isPending ? t('common.saving') : t('page.change_detail.unlink_asset')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
