import { useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { Badge, StatusBadge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Table, Th, Td } from '../../components/ui/Table';
import { formatDate, formatDateTime } from '../../lib/date';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import { AssetLabel } from '../../components/AssetLabel';
import { CustomFieldsDisplay } from '../../components/custom-fields/CustomFieldsDisplay';
import { CustomFieldsForm } from '../../components/custom-fields/CustomFieldsForm';
import type {
  Asset,
  AssetCheckout,
  AssetEvent,
  AssetLocation,
  AssetTypeDefinition,
  AssignableUser,
  AssetStatus,
  CustomFieldValue,
  MaintenanceRecord,
  PaginatedResponse,
  Shipment,
} from '../../types';

function toTitle(value: string): string {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatUnknown(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-';
  if (typeof value === 'string') {
    const dateLike = /^\d{4}-\d{2}-\d{2}/.test(value);
    return dateLike ? formatDate(value) : value;
  }
  return String(value);
}

function eventSummary(event: AssetEvent, t: (key: string, params?: Record<string, string | number>, options?: { defaultValue?: string }) => string): string {
  switch (event.event_type) {
    case 'created':
      return t('page.asset_detail.event_created');
    case 'updated':
      return t('page.asset_detail.event_updated');
    case 'assigned':
      return t('page.asset_detail.event_assigned');
    case 'unassigned':
      return t('page.asset_detail.event_unassigned');
    case 'location_changed':
      return t('page.asset_detail.event_location_changed');
    case 'status_changed': {
      const oldStatus = typeof event.data.old_status === 'string' ? event.data.old_status : null;
      const newStatus = typeof event.data.new_status === 'string' ? event.data.new_status : null;
      if (oldStatus && newStatus) {
        const oldLabel = t(`enum.${oldStatus}`, undefined, { defaultValue: toTitle(oldStatus) });
        const nextLabel = t(`enum.${newStatus}`, undefined, { defaultValue: toTitle(newStatus) });
        return t('page.asset_detail.event_status_changed', { old: oldLabel, next: nextLabel });
      }
      return t('page.asset_detail.event_status_changed_short');
    }
    default:
      return toTitle(event.event_type);
  }
}

function eventDetails(
  event: AssetEvent,
  userLabelById: (id: string) => string,
  t: (key: string, params?: Record<string, string | number>, options?: { defaultValue?: string }) => string,
): string {
  if (event.event_type === 'updated') {
    const updates = Object.entries(event.data)
      .map(([field, delta]) => {
        if (!delta || typeof delta !== 'object') return null;
        const oldValue = (delta as { old?: unknown }).old;
        const newValue = (delta as { new?: unknown }).new;
        return `${toTitle(field)}: ${formatUnknown(oldValue)} -> ${formatUnknown(newValue)}`;
      })
      .filter(Boolean);

    return updates.length ? updates.join(' | ') : t('page.asset_detail.no_field_changes');
  }

  if (event.event_type === 'assigned') {
    const userId = typeof event.data.user_id === 'string' ? event.data.user_id : null;
    const departmentId = typeof event.data.department_id === 'string' ? event.data.department_id : null;
    return `${t('page.asset_detail.assigned_user')}: ${userId ? userLabelById(userId) : '-'}${departmentId ? ` | ${t('page.asset_detail.department')}: ${departmentId}` : ''}`;
  }

  if (event.event_type === 'unassigned') {
    const previousUserId = typeof event.data.previous_user_id === 'string' ? event.data.previous_user_id : null;
    const reason = typeof event.data.reason === 'string' ? event.data.reason : null;
    if (reason) return `${t('page.asset_detail.reason')}: ${reason}`;
    if (previousUserId) return `${t('page.asset_detail.previous_user')}: ${userLabelById(previousUserId)}`;
    return t('page.asset_detail.unassigned_detail');
  }

  if (event.event_type === 'location_changed') {
    const oldLoc = typeof event.data.old_location_name === 'string' ? event.data.old_location_name : null;
    const newLoc = typeof event.data.new_location_name === 'string' ? event.data.new_location_name : null;
    const notes = typeof event.data.notes === 'string' ? event.data.notes : null;
    const parts: string[] = [];
    if (oldLoc || newLoc) parts.push(`${oldLoc || '-'} -> ${newLoc || '-'}`);
    if (notes) parts.push(notes);
    return parts.length ? parts.join(' | ') : t('page.asset_detail.event_location_changed');
  }

  if (event.event_type === 'created') {
    const type = typeof event.data.type === 'string' ? event.data.type : null;
    const serial = typeof event.data.serial_number === 'string' ? event.data.serial_number : null;
    return `${type ? `${t('table.type')}: ${t(`enum.${type}`, undefined, { defaultValue: toTitle(type) })}` : ''}${type && serial ? ' | ' : ''}${serial ? `${t('table.serial')}: ${serial}` : ''}` || t('page.asset_detail.asset_initialized');
  }

  if (event.event_type === 'status_changed') {
    const oldStatus = typeof event.data.old_status === 'string' ? event.data.old_status : null;
    const newStatus = typeof event.data.new_status === 'string' ? event.data.new_status : null;
    return t('page.asset_detail.status_from_to', {
      old: oldStatus ? t(`enum.${oldStatus}`, undefined, { defaultValue: toTitle(oldStatus) }) : '-',
      next: newStatus ? t(`enum.${newStatus}`, undefined, { defaultValue: toTitle(newStatus) }) : '-',
    });
  }

  return t('page.asset_detail.no_extra_details');
}

function cfToDict(fields: CustomFieldValue[] | null | undefined): Record<string, unknown> {
  if (!fields) return {};
  const dict: Record<string, unknown> = {};
  for (const f of fields) {
    if (f.value != null) dict[f.key] = f.value;
  }
  return dict;
}

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { t } = useI18n();
  const { isRole } = useAuth();
  const navigate = useNavigate();
  const canInviteUsers = isRole('admin', 'super_admin');

  const [assignUserId, setAssignUserId] = useState('');
  const [moveLocationId, setMoveLocationId] = useState('');
  const [moveNotes, setMoveNotes] = useState('');
  const [unassignModalOpen, setUnassignModalOpen] = useState(false);
  const [unassignLocationId, setUnassignLocationId] = useState('');
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    type: '',
    brand: '',
    model: '',
    purchase_date: '',
    warranty_expiration: '',
    notes: '',
  });
  const [editCustomFields, setEditCustomFields] = useState<Record<string, unknown>>({});
  const [checkoutUserId, setCheckoutUserId] = useState('');
  const [checkoutCondition, setCheckoutCondition] = useState('');
  const [checkoutNotes, setCheckoutNotes] = useState('');
  const [showCheckinForm, setShowCheckinForm] = useState(false);
  const [checkinCondition, setCheckinCondition] = useState('');
  const [checkinNotes, setCheckinNotes] = useState('');
  const [showCancelForm, setShowCancelForm] = useState(false);
  const [cancelReason, setCancelReason] = useState('');

  const { data: asset, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['asset', id],
    queryFn: async () => {
      const { data } = await api.get(`/assets/${id}`);
      return data.data as Asset;
    },
    enabled: Boolean(id),
  });

  const { data: events } = useQuery({
    queryKey: ['asset-events', id],
    queryFn: async () => {
      const { data } = await api.get(`/assets/${id}/history`);
      return data.data as AssetEvent[];
    },
    enabled: Boolean(id),
  });

  const { data: shipments } = useQuery({
    queryKey: ['asset-shipments', id],
    queryFn: async () => {
      const { data } = await api.get(`/shipments/by-asset/${id}`);
      return data.data as Shipment[];
    },
    enabled: Boolean(id),
  });

  const { data: maintenanceHistory } = useQuery({
    queryKey: ['asset-maintenance', id],
    queryFn: async () => {
      const { data } = await api.get('/maintenance', {
        params: { asset_id: id, page: 1, page_size: 20 },
      });
      return data as PaginatedResponse<MaintenanceRecord>;
    },
    enabled: Boolean(id),
  });

  const { data: currentCheckout } = useQuery({
    queryKey: ['asset-checkout-current', id],
    queryFn: async () => {
      const { data } = await api.get(`/checkouts/assets/${id}/current`);
      return data.data as AssetCheckout | null;
    },
    enabled: Boolean(id),
  });

  const { data: checkoutHistory } = useQuery({
    queryKey: ['asset-checkout-history', id],
    queryFn: async () => {
      const { data } = await api.get(`/checkouts/assets/${id}`, {
        params: { page: 1, page_size: 20 },
      });
      return data as PaginatedResponse<AssetCheckout>;
    },
    enabled: Boolean(id),
  });

  const { data: locations } = useQuery({
    queryKey: ['locations'],
    queryFn: async () => {
      const { data } = await api.get('/assets/locations');
      return data.data as AssetLocation[];
    },
  });

  const { data: assetTypes } = useQuery({
    queryKey: ['asset-types-active'],
    queryFn: async () => {
      const { data } = await api.get('/asset-types', { params: { active_only: true } });
      return data.data as AssetTypeDefinition[];
    },
  });

  const {
    data: assignableUsers,
    refetch: refetchAssignableUsers,
  } = useQuery({
    queryKey: ['asset-assignable-users'],
    queryFn: async () => {
      const { data } = await api.get('/assets/assignable-users');
      return data.data as AssignableUser[];
    },
    staleTime: 0,
    refetchOnMount: 'always',
    refetchInterval: 15000,
  });

  const userEmailById = useMemo(
    () => new Map((assignableUsers ?? []).map((u) => [u.id, u.email])),
    [assignableUsers],
  );

  const refreshAssetQueries = () => {
    queryClient.invalidateQueries({ queryKey: ['asset', id] });
    queryClient.invalidateQueries({ queryKey: ['asset-events', id] });
    queryClient.invalidateQueries({ queryKey: ['asset-checkout-current', id] });
    queryClient.invalidateQueries({ queryKey: ['asset-checkout-history', id] });
    queryClient.invalidateQueries({ queryKey: ['assets'] });
  };

  const updateAsset = useMutation({
    mutationFn: () => {
      const payload: Record<string, unknown> = {
        type: editForm.type,
        brand: editForm.brand.trim(),
        model: editForm.model.trim(),
        purchase_date: editForm.purchase_date || null,
        warranty_expiration: editForm.warranty_expiration || null,
        notes: editForm.notes.trim() || null,
        custom_fields_data: Object.keys(editCustomFields).length ? editCustomFields : undefined,
      };
      return api.put(`/assets/${id}`, payload);
    },
    onSuccess: () => {
      refreshAssetQueries();
      setIsEditing(false);
      showToast({ title: t('page.asset_detail.toast_asset_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.asset_detail.error_update_asset');
      showToast({ title: t('page.asset_detail.error_update_failed'), description: detail, variant: 'error' });
    },
  });

  const changeStatus = useMutation({
    mutationFn: (status: AssetStatus) => api.patch(`/assets/${id}/status`, { status }),
    onSuccess: () => {
      refreshAssetQueries();
      showToast({ title: t('page.asset_detail.toast_status_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.asset_detail.error_update_status');
      showToast({ title: t('page.asset_detail.error_status_failed'), description: detail, variant: 'error' });
    },
  });

  const assignAsset = useMutation({
    mutationFn: (userId: string) => api.patch(`/assets/${id}/assign`, { user_id: userId }),
    onSuccess: () => {
      refreshAssetQueries();
      showToast({ title: t('page.asset_detail.toast_assigned'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.asset_detail.error_assign');
      showToast({ title: t('page.asset_detail.error_assignment_failed'), description: detail, variant: 'error' });
    },
  });

  const unassignAsset = useMutation({
    mutationFn: async () => {
      await api.patch(`/assets/${id}/unassign`);
      if (unassignLocationId) {
        await api.patch(`/assets/${id}/move`, { location_id: unassignLocationId });
      }
    },
    onSuccess: () => {
      refreshAssetQueries();
      setUnassignModalOpen(false);
      setUnassignLocationId('');
      showToast({ title: t('page.asset_detail.toast_unassigned'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.asset_detail.error_unassign');
      showToast({ title: t('page.asset_detail.error_unassign_failed'), description: detail, variant: 'error' });
    },
  });

  const moveAsset = useMutation({
    mutationFn: (payload: { location_id: string; notes?: string }) => api.patch(`/assets/${id}/move`, payload),
    onSuccess: () => {
      refreshAssetQueries();
      setMoveLocationId('');
      setMoveNotes('');
      showToast({ title: t('page.asset_detail.toast_moved'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.asset_detail.error_move');
      showToast({ title: t('page.asset_detail.error_move_failed'), description: detail, variant: 'error' });
    },
  });

  const inviteAssignableUser = useMutation({
    mutationFn: (email: string) => api.post('/users/invite', { email }),
    onSuccess: async (_res, email) => {
      const normalized = email.trim().toLowerCase();
      setInviteModalOpen(false);
      setInviteEmail('');
      showToast({
        title: t('page.users.toast_invitation_sent'),
        description: t('page.users.toast_invitation_desc'),
        variant: 'success',
      });

      const refreshed = await refetchAssignableUsers();
      const invitedUser = (refreshed.data ?? []).find(
        (user) => user.email.toLowerCase() === normalized,
      );

      if (invitedUser) {
        setAssignUserId(invitedUser.id);
        showToast({
          title: t('page.asset_detail.toast_invited_selected'),
          description: invitedUser.email,
          variant: 'info',
        });
        return;
      }

      showToast({
        title: t('page.asset_detail.toast_invited_refresh_needed'),
        variant: 'info',
      });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.users.error_invite');
      showToast({ title: t('page.users.error_invite_title'), description: detail, variant: 'error' });
    },
  });

  const createCheckout = useMutation({
    mutationFn: (payload: { user_id: string; condition_out: string; notes_out?: string }) =>
      api.post(`/checkouts/assets/${id}`, payload),
    onSuccess: () => {
      refreshAssetQueries();
      setCheckoutUserId('');
      setCheckoutCondition('');
      setCheckoutNotes('');
      showToast({ title: t('page.asset_detail.toast_checkout_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.asset_detail.error_checkout');
      showToast({ title: t('page.asset_detail.error_checkout_failed'), description: detail, variant: 'error' });
    },
  });

  const checkinAsset = useMutation({
    mutationFn: (payload: { condition_in: string; notes_in?: string }) =>
      api.post(`/checkouts/assets/${id}/checkin`, payload),
    onSuccess: () => {
      refreshAssetQueries();
      setShowCheckinForm(false);
      setCheckinCondition('');
      setCheckinNotes('');
      showToast({ title: t('page.asset_detail.toast_checkin_success'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.asset_detail.error_checkin');
      showToast({ title: t('page.asset_detail.error_checkin_failed'), description: detail, variant: 'error' });
    },
  });

  const cancelCheckout = useMutation({
    mutationFn: (payload: { reason?: string }) =>
      api.post(`/checkouts/assets/${id}/cancel`, payload),
    onSuccess: () => {
      refreshAssetQueries();
      setShowCancelForm(false);
      setCancelReason('');
      showToast({ title: t('page.asset_detail.toast_cancel_success'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.asset_detail.error_cancel');
      showToast({ title: t('page.asset_detail.error_cancel_failed'), description: detail, variant: 'error' });
    },
  });

  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <ErrorState
        message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }
  if (!asset) return <ErrorState message={t('page.asset_detail.not_found')} />;

  const assignedLabel = asset.assigned_to_email || (asset.assigned_to ? userEmailById.get(asset.assigned_to) || asset.assigned_to : null);
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <Card>
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">{asset.brand} {asset.model}</h2>
            <p className="mt-1 text-xs text-muted-foreground">Serial: {asset.serial_number}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setEditForm({
                  type: asset.type,
                  brand: asset.brand,
                  model: asset.model,
                  purchase_date: asset.purchase_date ?? '',
                  warranty_expiration: asset.warranty_expiration ?? '',
                  notes: asset.notes ?? '',
                });
                setEditCustomFields(cfToDict(asset.custom_fields));
                setIsEditing(true);
              }}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
            >
              {t('page.asset_detail.edit_asset')}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
          <div><span className="text-muted-foreground">{t('table.type')}:</span> {t(`enum.${asset.type}`)}</div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">{t('table.status')}:</span>
            <StatusBadge status={asset.status} />
          </div>
          <div><span className="text-muted-foreground">{t('table.assigned_to')}:</span> {assignedLabel || '-'}</div>
          <div><span className="text-muted-foreground">{t('page.asset_detail.location')}:</span> {asset.location_name || '-'}</div>
          <div><span className="text-muted-foreground">{t('table.purchase_date')}:</span> {formatDate(asset.purchase_date)}</div>
          <div><span className="text-muted-foreground">{t('table.warranty')}:</span> {formatDate(asset.warranty_expiration)}</div>
          <div><span className="text-muted-foreground">{t('table.updated')}:</span> {formatDateTime(asset.updated_at)}</div>
        </div>

        {asset.notes && <p className="mt-4 rounded bg-secondary p-3 text-sm text-muted-foreground">{asset.notes}</p>}

        {asset.custom_fields && asset.custom_fields.length > 0 && (
          <div className="mt-4">
            <h3 className="mb-2 text-sm font-semibold text-foreground">{t('page.custom_fields.section_title')}</h3>
            <CustomFieldsDisplay customFields={asset.custom_fields} />
          </div>
        )}
      </Card>

      <AssetLabel
        assetId={id!}
        serialNumber={asset.serial_number}
        brand={asset.brand}
        model={asset.model}
      />

      <Card>
        <h3 className="mb-3 text-sm font-semibold text-foreground">{t('page.asset_detail.assignment')}</h3>
        {asset.assigned_to ? (
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-sm text-foreground">{t('table.assigned_to')} <span className="font-medium">{assignedLabel || asset.assigned_to}</span></p>
            <button
              type="button"
              onClick={() => setUnassignModalOpen(true)}
              disabled={unassignAsset.isPending}
              className="rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50"
            >
              {unassignAsset.isPending ? t('page.asset_detail.unassigning') : t('page.asset_detail.unassign')}
            </button>
            {asset.status !== 'decommissioned' && (
              <button
                type="button"
                onClick={() => changeStatus.mutate('decommissioned')}
                disabled={changeStatus.isPending}
                className="rounded-md h-9 px-4 text-sm font-medium border border-border bg-background text-foreground shadow-xs hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
              >
                {changeStatus.isPending ? t('auth.set_password.saving') : t('page.asset_detail.decommission')}
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            <label className="block text-muted-foreground">{t('page.asset_detail.assign_to_user')}</label>
            <div className="flex flex-wrap items-center gap-3">
              <select
                value={assignUserId}
                onChange={(e) => setAssignUserId(e.target.value)}
                className="min-w-64 text-sm"
              >
                <option value="">{t('page.asset_detail.select_user')}</option>
                {(assignableUsers ?? []).map((u) => (
                  <option key={u.id} value={u.id}>{u.email}{u.name ? ` (${u.name})` : ''}</option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => assignAsset.mutate(assignUserId)}
                disabled={!assignUserId || assignAsset.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {assignAsset.isPending ? t('page.asset_detail.assigning') : t('page.asset_detail.assign')}
              </button>
              {asset.status !== 'decommissioned' && (
                <button
                  type="button"
                  onClick={() => changeStatus.mutate('decommissioned')}
                  disabled={changeStatus.isPending}
                  className="rounded-md h-9 px-4 text-sm font-medium border border-border bg-background text-foreground shadow-xs hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
                >
                  {changeStatus.isPending ? t('auth.set_password.saving') : t('page.asset_detail.decommission')}
                </button>
              )}
            </div>
            {canInviteUsers && (
              <button
                type="button"
                onClick={() => setInviteModalOpen(true)}
                className="text-xs text-primary hover:underline"
              >
                {t('page.asset_detail.invite_user')}
              </button>
            )}
          </div>
        )}
      </Card>

      {asset.status !== 'decommissioned' && (
        <Card>
          <h3 className="mb-3 text-sm font-semibold text-foreground">{t('page.asset_detail.move_asset')}</h3>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex items-center gap-2 self-center text-sm text-foreground">
              <span className="text-muted-foreground">{t('page.asset_detail.location')}:</span>
              <span className="font-medium">{asset.location_name || '—'}</span>
              <span className="text-muted-foreground">→</span>
            </div>
            <div>
              <label className="block mb-1.5 text-muted-foreground">{t('page.asset_detail.move_to_location')}</label>
              <select
                value={moveLocationId}
                onChange={(e) => setMoveLocationId(e.target.value)}
                className="min-w-64 text-sm"
              >
                <option value="">{t('page.asset_detail.select_location')}</option>
                {(locations ?? []).map((loc) => (
                  <option key={loc.id} value={loc.id}>{loc.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block mb-1.5 text-muted-foreground">{t('page.asset_detail.move_notes')}</label>
              <input
                type="text"
                value={moveNotes}
                onChange={(e) => setMoveNotes(e.target.value)}
                className="min-w-64 text-sm"
              />
            </div>
            <button
              type="button"
              onClick={() => moveAsset.mutate({ location_id: moveLocationId, ...(moveNotes.trim() ? { notes: moveNotes.trim() } : {}) })}
              disabled={!moveLocationId || moveLocationId === asset.location_id || moveAsset.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {moveAsset.isPending ? t('page.asset_detail.moving') : t('page.asset_detail.move')}
            </button>
          </div>
        </Card>
      )}

      {/* Custody Section */}
      <Card>
        <h3 className="mb-3 text-sm font-semibold text-foreground">{t('page.asset_detail.custody')}</h3>
        {currentCheckout ? (
          <div className="space-y-4">
            <div className="rounded-md border border-border bg-secondary/50 p-4">
              <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                <div>
                  <span className="text-muted-foreground">{t('page.asset_detail.checkout_user')}:</span>{' '}
                  <span className="font-medium">{userEmailById.get(currentCheckout.user_id) || currentCheckout.user_id}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">{t('page.asset_detail.checkout_date')}:</span>{' '}
                  <span className="font-medium">{formatDateTime(currentCheckout.checked_out_at)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">{t('page.asset_detail.condition_out')}:</span>{' '}
                  <Badge variant="default">{t(`enum.${currentCheckout.condition_out}`)}</Badge>
                </div>
                <div>
                  <span className="text-muted-foreground">{t('page.asset_detail.acceptance_status')}:</span>{' '}
                  {currentCheckout.accepted_at ? (
                    <Badge variant="success">{t('page.asset_detail.accepted')}</Badge>
                  ) : (
                    <Badge variant="warning">{t('page.asset_detail.pending_acceptance')}</Badge>
                  )}
                </div>
                {currentCheckout.auto_assigned && (
                  <div>
                    <Badge variant="info">{t('page.asset_detail.auto_assigned')}</Badge>
                  </div>
                )}
              </div>
            </div>

            {/* Checkin form */}
            {showCheckinForm ? (
              <div className="rounded-md border border-border bg-background p-4 space-y-3">
                <h4 className="text-sm font-medium text-foreground">{t('page.asset_detail.checkin_asset')}</h4>
                <div className="flex flex-wrap items-end gap-3">
                  <div>
                    <label className="block mb-1.5 text-xs text-muted-foreground">{t('page.asset_detail.select_condition')}</label>
                    <select value={checkinCondition} onChange={(e) => setCheckinCondition(e.target.value)} className="min-w-48 text-sm">
                      <option value="">{t('page.asset_detail.select_condition')}</option>
                      {['new', 'good', 'fair', 'damaged', 'unusable'].map((c) => (
                        <option key={c} value={c}>{t(`enum.${c}`)}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block mb-1.5 text-xs text-muted-foreground">{t('page.asset_detail.checkin_notes')}</label>
                    <input type="text" value={checkinNotes} onChange={(e) => setCheckinNotes(e.target.value)} className="min-w-48 text-sm" />
                  </div>
                  <button
                    type="button"
                    onClick={() => checkinAsset.mutate({ condition_in: checkinCondition, ...(checkinNotes.trim() ? { notes_in: checkinNotes.trim() } : {}) })}
                    disabled={!checkinCondition || checkinAsset.isPending}
                    className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                  >
                    {checkinAsset.isPending ? t('auth.set_password.saving') : t('page.asset_detail.checkin_asset')}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setShowCheckinForm(false); setCheckinCondition(''); setCheckinNotes(''); }}
                    className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
                  >
                    {t('common.cancel')}
                  </button>
                </div>
              </div>
            ) : showCancelForm ? (
              <div className="rounded-md border border-border bg-background p-4 space-y-3">
                <h4 className="text-sm font-medium text-foreground">{t('page.asset_detail.cancel_checkout')}</h4>
                <div className="flex flex-wrap items-end gap-3">
                  <div>
                    <label className="block mb-1.5 text-xs text-muted-foreground">{t('page.asset_detail.cancel_reason')}</label>
                    <input type="text" value={cancelReason} onChange={(e) => setCancelReason(e.target.value)} className="min-w-64 text-sm" />
                  </div>
                  <button
                    type="button"
                    onClick={() => cancelCheckout.mutate({ reason: cancelReason.trim() || undefined })}
                    disabled={cancelCheckout.isPending}
                    className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:pointer-events-none disabled:opacity-50"
                  >
                    {cancelCheckout.isPending ? t('auth.set_password.saving') : t('page.asset_detail.cancel_checkout')}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setShowCancelForm(false); setCancelReason(''); }}
                    className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
                  >
                    {t('common.cancel')}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setShowCheckinForm(true)}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
                >
                  {t('page.asset_detail.checkin_asset')}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCancelForm(true)}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border border-destructive text-destructive bg-background shadow-xs hover:bg-destructive/10 transition-all"
                >
                  {t('page.asset_detail.cancel_checkout')}
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">{t('page.asset_detail.no_active_checkout')}</p>
            {asset.status !== 'decommissioned' && (
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('page.asset_detail.checkout_user')}</label>
                  <select value={checkoutUserId} onChange={(e) => setCheckoutUserId(e.target.value)} className="min-w-64 text-sm">
                    <option value="">{t('page.asset_detail.select_user')}</option>
                    {(assignableUsers ?? []).map((u) => (
                      <option key={u.id} value={u.id}>{u.email}{u.name ? ` (${u.name})` : ''}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('page.asset_detail.select_condition')}</label>
                  <select value={checkoutCondition} onChange={(e) => setCheckoutCondition(e.target.value)} className="min-w-48 text-sm">
                    <option value="">{t('page.asset_detail.select_condition')}</option>
                    {['new', 'good', 'fair', 'damaged', 'unusable'].map((c) => (
                      <option key={c} value={c}>{t(`enum.${c}`)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('table.notes')}</label>
                  <input type="text" value={checkoutNotes} onChange={(e) => setCheckoutNotes(e.target.value)} className="min-w-48 text-sm" />
                </div>
                <button
                  type="button"
                  onClick={() => createCheckout.mutate({
                    user_id: checkoutUserId,
                    condition_out: checkoutCondition,
                    ...(checkoutNotes.trim() ? { notes_out: checkoutNotes.trim() } : {}),
                  })}
                  disabled={!checkoutUserId || !checkoutCondition || createCheckout.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {createCheckout.isPending ? t('auth.set_password.saving') : t('page.asset_detail.checkout_asset')}
                </button>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Checkout History */}
      <Card>
        <h3 className="mb-3 text-sm font-semibold text-foreground">{t('page.asset_detail.checkout_history')}</h3>
        {!checkoutHistory?.data.length ? (
          <p className="text-sm text-muted-foreground">{t('page.asset_detail.no_checkout_history')}</p>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>{t('page.asset_detail.checkout_user')}</Th>
                <Th>{t('page.asset_detail.condition_out')}</Th>
                <Th>{t('page.asset_detail.checkout_date')}</Th>
                <Th>{t('table.status')}</Th>
                <Th>{t('page.asset_detail.condition_in')}</Th>
                <Th>{t('page.asset_detail.checked_in_at')}</Th>
              </tr>
            </thead>
            <tbody>
              {checkoutHistory.data.map((co) => (
                <tr key={co.id}>
                  <Td>{userEmailById.get(co.user_id) || co.user_id}</Td>
                  <Td><Badge variant="default">{t(`enum.${co.condition_out}`)}</Badge></Td>
                  <Td>{formatDateTime(co.checked_out_at)}</Td>
                  <Td><StatusBadge status={co.status} /></Td>
                  <Td>{co.condition_in ? <Badge variant="default">{t(`enum.${co.condition_in}`)}</Badge> : '—'}</Td>
                  <Td>{co.checked_in_at ? formatDateTime(co.checked_in_at) : '—'}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Card>
        <h3 className="mb-3 text-sm font-semibold text-foreground">{t('page.asset_detail.event_history')}</h3>
        {!events?.length ? (
          <p className="text-sm text-muted-foreground">{t('page.asset_detail.no_events')}</p>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>{t('table.event')}</Th>
                <Th>{t('table.by')}</Th>
                <Th>{t('table.date')}</Th>
                <Th>{t('table.details')}</Th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => {
                const actor = event.performed_by_email || userEmailById.get(event.performed_by) || event.performed_by;
                const userLabelById = (userId: string) => userEmailById.get(userId) || userId;
                return (
                  <tr key={event.id}>
                    <Td>{eventSummary(event, t)}</Td>
                    <Td>{actor}</Td>
                    <Td>{formatDateTime(event.created_at)}</Td>
                    <Td>
                      <div className="max-w-xl whitespace-normal text-xs text-muted-foreground">{eventDetails(event, userLabelById, t)}</div>
                    </Td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        )}
      </Card>

      <Card>
        <h3 className="mb-3 text-sm font-semibold text-foreground">{t('page.asset_detail.shipment_history')}</h3>
        {!shipments?.length ? (
          <p className="text-sm text-muted-foreground">{t('page.asset_detail.no_shipments')}</p>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>{t('table.direction')}</Th>
                <Th>{t('table.destination')}</Th>
                <Th>{t('table.carrier')}</Th>
                <Th>{t('table.status')}</Th>
                <Th>{t('table.dispatched')}</Th>
                <Th>{t('table.delivered')}</Th>
              </tr>
            </thead>
            <tbody>
              {shipments.map((s) => (
                <tr key={s.id} className="cursor-pointer hover:bg-secondary" onClick={() => navigate(`/shipments/${s.id}`)}>
                  <Td><Badge variant={s.direction === 'outbound' ? 'info' : 'warning'}>{t(`enum.shipment_direction.${s.direction}`)}</Badge></Td>
                  <Td>{t(`enum.destination_type.${s.destination_type}`)}</Td>
                  <Td>{s.carrier || '—'}</Td>
                  <Td><StatusBadge status={s.status} /></Td>
                  <Td>{s.dispatched_at ? formatDateTime(s.dispatched_at) : '—'}</Td>
                  <Td>{s.delivered_at ? formatDateTime(s.delivered_at) : '—'}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Card>
        <h3 className="mb-3 text-sm font-semibold text-foreground">{t('page.asset_detail.maintenance_history')}</h3>
        {!maintenanceHistory?.data.length ? (
          <p className="text-sm text-muted-foreground">{t('page.asset_detail.no_maintenance')}</p>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>{t('table.status')}</Th>
                <Th>{t('table.priority')}</Th>
                <Th>{t('table.title')}</Th>
                <Th>{t('table.date')}</Th>
              </tr>
            </thead>
            <tbody>
              {maintenanceHistory.data.map((m) => (
                <tr key={m.id} className="cursor-pointer hover:bg-secondary" onClick={() => navigate(`/maintenance/${m.id}`)}>
                  <Td><Badge variant="default">{t(`enum.maintenance_status.${m.status.toLowerCase()}`)}</Badge></Td>
                  <Td>{t(`enum.maintenance_priority.${m.priority.toLowerCase()}`)}</Td>
                  <Td>{m.title}</Td>
                  <Td>{m.scheduled_at ? formatDateTime(m.scheduled_at) : '—'}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      {isEditing && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (!updateAsset.isPending) setIsEditing(false);
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-lg max-h-[90vh] flex flex-col rounded-xl border border-border bg-card shadow-lg">
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <h3 className="text-lg font-semibold text-foreground">{t('page.asset_detail.edit_asset')}</h3>
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                disabled={updateAsset.isPending}
                className="text-muted-foreground hover:text-foreground text-xl leading-none"
              >
                &times;
              </button>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                updateAsset.mutate();
              }}
              className="flex flex-col overflow-hidden"
            >
              <div className="overflow-y-auto px-6 py-4 space-y-3">
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('table.type')}</label>
                  <select
                    value={editForm.type}
                    onChange={(e) => setEditForm((prev) => ({ ...prev, type: e.target.value }))}
                    className="w-full"
                  >
                    {(assetTypes ?? []).map((at) => (
                      <option key={at.code} value={at.code}>{at.name}</option>
                    ))}
                    {assetTypes && !assetTypes.some((at) => at.code === editForm.type) && (
                      <option value={editForm.type}>{editForm.type}</option>
                    )}
                  </select>
                </div>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div>
                    <label className="block mb-1.5 text-muted-foreground">{t('table.brand')}</label>
                    <input
                      value={editForm.brand}
                      onChange={(e) => setEditForm((prev) => ({ ...prev, brand: e.target.value }))}
                      required
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="block mb-1.5 text-muted-foreground">{t('table.model')}</label>
                    <input
                      value={editForm.model}
                      onChange={(e) => setEditForm((prev) => ({ ...prev, model: e.target.value }))}
                      required
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="block mb-1.5 text-muted-foreground">{t('table.purchase_date')}</label>
                    <input
                      type="date"
                      value={editForm.purchase_date}
                      onChange={(e) => setEditForm((prev) => ({ ...prev, purchase_date: e.target.value }))}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="block mb-1.5 text-muted-foreground">{t('table.warranty_expiration')}</label>
                    <input
                      type="date"
                      value={editForm.warranty_expiration}
                      onChange={(e) => setEditForm((prev) => ({ ...prev, warranty_expiration: e.target.value }))}
                      className="w-full"
                    />
                  </div>
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('table.notes')}</label>
                  <textarea
                    rows={3}
                    value={editForm.notes}
                    onChange={(e) => setEditForm((prev) => ({ ...prev, notes: e.target.value }))}
                    className="w-full"
                  />
                </div>
                <CustomFieldsForm
                  entityType="asset"
                  values={editCustomFields}
                  onChange={setEditCustomFields}
                />
              </div>
              <div className="flex justify-end gap-2 border-t border-border px-6 py-4">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  disabled={updateAsset.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={updateAsset.isPending || !editForm.brand.trim() || !editForm.model.trim()}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {updateAsset.isPending ? t('auth.set_password.saving') : t('page.asset_detail.save_changes')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {unassignModalOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (!unassignAsset.isPending) {
                setUnassignModalOpen(false);
                setUnassignLocationId('');
              }
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.asset_detail.unassign')}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{t('page.asset_detail.unassign_modal_desc')}</p>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.asset_detail.new_location')}</label>
                <select
                  value={unassignLocationId}
                  onChange={(e) => setUnassignLocationId(e.target.value)}
                  className="w-full text-sm"
                >
                  <option value="">{t('page.asset_detail.no_location_change')}</option>
                  {(locations ?? []).map((loc) => (
                    <option key={loc.id} value={loc.id}>{loc.name}</option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setUnassignModalOpen(false);
                    setUnassignLocationId('');
                  }}
                  disabled={unassignAsset.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="button"
                  onClick={() => unassignAsset.mutate()}
                  disabled={unassignAsset.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {unassignAsset.isPending ? t('page.asset_detail.unassigning') : t('page.asset_detail.confirm_unassign')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {inviteModalOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (!inviteAssignableUser.isPending) setInviteModalOpen(false);
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.asset_detail.invite_user')}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{t('page.asset_detail.invite_modal_desc')}</p>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!inviteEmail.trim()) return;
                inviteAssignableUser.mutate(inviteEmail.trim());
              }}
              className="mt-4 space-y-4"
            >
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('table.email')}</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder={t('common.placeholder_user_email')}
                  required
                  autoFocus
                  className="w-full"
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setInviteModalOpen(false)}
                  disabled={inviteAssignableUser.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={inviteAssignableUser.isPending || !inviteEmail.trim()}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {inviteAssignableUser.isPending ? t('auth.login.sending') : t('page.asset_detail.invite_and_select')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
