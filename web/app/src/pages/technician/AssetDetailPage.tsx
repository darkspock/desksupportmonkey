import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Table, Th, Td } from '../../components/ui/Table';
import { formatDate, formatDateTime } from '../../lib/date';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { Asset, AssetEvent, AssignableUser, AssetStatus } from '../../types';

const STATUS_OPTIONS: AssetStatus[] = ['in_stock', 'assigned', 'in_repair', 'decommissioned'];

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

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { t } = useI18n();
  const { isRole } = useAuth();
  const canInviteUsers = isRole('admin', 'super_admin');

  const [assignUserId, setAssignUserId] = useState('');
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [statusValue, setStatusValue] = useState<AssetStatus | null>(null);
  const [editForm, setEditForm] = useState({
    brand: '',
    model: '',
    purchase_date: '',
    warranty_expiration: '',
    notes: '',
  });

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
    queryClient.invalidateQueries({ queryKey: ['assets'] });
  };

  const updateAsset = useMutation({
    mutationFn: () => {
      const payload: Record<string, string | null> = {
        brand: editForm.brand.trim(),
        model: editForm.model.trim(),
        purchase_date: editForm.purchase_date || null,
        warranty_expiration: editForm.warranty_expiration || null,
        notes: editForm.notes.trim() || null,
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
      if (asset) setStatusValue(asset.status);
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
    mutationFn: () => api.patch(`/assets/${id}/unassign`),
    onSuccess: () => {
      refreshAssetQueries();
      showToast({ title: t('page.asset_detail.toast_unassigned'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.asset_detail.error_unassign');
      showToast({ title: t('page.asset_detail.error_unassign_failed'), description: detail, variant: 'error' });
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
  const selectedStatus = statusValue ?? asset.status;

  return (
    <div className="max-w-5xl space-y-6">
      <Card>
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{asset.brand} {asset.model}</h2>
            <p className="mt-1 text-xs text-gray-500">Serial: {asset.serial_number}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                if (isEditing) {
                  setIsEditing(false);
                  return;
                }
                setEditForm({
                  brand: asset.brand,
                  model: asset.model,
                  purchase_date: asset.purchase_date ?? '',
                  warranty_expiration: asset.warranty_expiration ?? '',
                  notes: asset.notes ?? '',
                });
                setIsEditing(true);
              }}
              className="rounded border px-3 py-1.5 text-sm hover:bg-gray-50"
            >
              {isEditing ? t('common.cancel') : t('page.asset_detail.edit_asset')}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
          <div><span className="text-gray-500">{t('table.type')}:</span> {t(`enum.${asset.type}`)}</div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">{t('table.status')}:</span>
            <StatusBadge status={asset.status} />
          </div>
          <div><span className="text-gray-500">{t('table.assigned_to')}:</span> {assignedLabel || '-'}</div>
          <div><span className="text-gray-500">{t('table.purchase_date')}:</span> {formatDate(asset.purchase_date)}</div>
          <div><span className="text-gray-500">{t('table.warranty')}:</span> {formatDate(asset.warranty_expiration)}</div>
          <div><span className="text-gray-500">{t('table.updated')}:</span> {formatDateTime(asset.updated_at)}</div>
        </div>

        {asset.notes && <p className="mt-4 rounded bg-gray-50 p-3 text-sm text-gray-600">{asset.notes}</p>}
      </Card>

      <Card>
        <h3 className="mb-3 text-sm font-semibold text-gray-900">{t('table.status')}</h3>
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <label className="mb-1 block text-xs text-gray-500">{t('page.asset_detail.change_status')}</label>
            <select
              value={selectedStatus}
              onChange={(e) => setStatusValue(e.target.value as AssetStatus)}
              className="rounded border px-3 py-2 text-sm"
            >
              {STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>{t(`enum.${status}`)}</option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={() => changeStatus.mutate(selectedStatus)}
            disabled={changeStatus.isPending || selectedStatus === asset.status}
            className="rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {changeStatus.isPending ? t('auth.set_password.saving') : t('page.asset_detail.update_status')}
          </button>
        </div>
      </Card>

      <Card>
        <h3 className="mb-3 text-sm font-semibold text-gray-900">{t('page.asset_detail.assignment')}</h3>
        {asset.assigned_to ? (
          <div className="flex flex-wrap items-end gap-3">
            <p className="text-sm text-gray-700">{t('table.assigned_to')} <span className="font-medium">{assignedLabel || asset.assigned_to}</span></p>
            <button
              type="button"
              onClick={() => unassignAsset.mutate()}
              disabled={unassignAsset.isPending}
              className="rounded border border-red-200 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
            >
              {unassignAsset.isPending ? t('page.asset_detail.unassigning') : t('page.asset_detail.unassign')}
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-start gap-2">
            <div>
              <label className="mb-1 block text-xs text-gray-500">{t('page.asset_detail.assign_to_user')}</label>
              <select
                value={assignUserId}
                onChange={(e) => setAssignUserId(e.target.value)}
                className="min-w-64 rounded border px-3 py-2 text-sm"
              >
                <option value="">{t('page.asset_detail.select_user')}</option>
                {(assignableUsers ?? []).map((u) => (
                  <option key={u.id} value={u.id}>{u.email}{u.name ? ` (${u.name})` : ''}</option>
                ))}
              </select>
              {canInviteUsers && (
                <button
                  type="button"
                  onClick={() => setInviteModalOpen(true)}
                  className="mt-2 block text-left text-xs text-blue-600 hover:underline"
                >
                  {t('page.asset_detail.invite_user')}
                </button>
              )}
            </div>
            <button
              type="button"
              onClick={() => assignAsset.mutate(assignUserId)}
              disabled={!assignUserId || assignAsset.isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {assignAsset.isPending ? t('page.asset_detail.assigning') : t('page.asset_detail.assign')}
            </button>
          </div>
        )}
      </Card>

      {isEditing && (
        <Card>
          <h3 className="mb-3 text-sm font-semibold text-gray-900">{t('page.asset_detail.edit_asset')}</h3>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              updateAsset.mutate();
            }}
            className="space-y-3"
          >
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-gray-500">{t('table.brand')}</label>
                <input
                  value={editForm.brand}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, brand: e.target.value }))}
                  required
                  className="w-full rounded border px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500">{t('table.model')}</label>
                <input
                  value={editForm.model}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, model: e.target.value }))}
                  required
                  className="w-full rounded border px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500">{t('table.purchase_date')}</label>
                <input
                  type="date"
                  value={editForm.purchase_date}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, purchase_date: e.target.value }))}
                  className="w-full rounded border px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500">{t('table.warranty_expiration')}</label>
                <input
                  type="date"
                  value={editForm.warranty_expiration}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, warranty_expiration: e.target.value }))}
                  className="w-full rounded border px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">{t('table.notes')}</label>
              <textarea
                rows={3}
                value={editForm.notes}
                onChange={(e) => setEditForm((prev) => ({ ...prev, notes: e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={updateAsset.isPending || !editForm.brand.trim() || !editForm.model.trim()}
                className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {updateAsset.isPending ? t('auth.set_password.saving') : t('page.asset_detail.save_changes')}
              </button>
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="rounded border px-4 py-2 text-sm hover:bg-gray-50"
              >
                {t('common.cancel')}
              </button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        <h3 className="mb-3 text-sm font-semibold text-gray-900">{t('page.asset_detail.event_history')}</h3>
        {!events?.length ? (
          <p className="text-sm text-gray-400">{t('page.asset_detail.no_events')}</p>
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
            <tbody className="divide-y divide-gray-100">
              {events.map((event) => {
                const actor = event.performed_by_email || userEmailById.get(event.performed_by) || event.performed_by;
                const userLabelById = (userId: string) => userEmailById.get(userId) || userId;
                return (
                  <tr key={event.id}>
                    <Td>{eventSummary(event, t)}</Td>
                    <Td>{actor}</Td>
                    <Td>{formatDateTime(event.created_at)}</Td>
                    <Td>
                      <div className="max-w-xl whitespace-normal text-xs text-gray-600">{eventDetails(event, userLabelById, t)}</div>
                    </Td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        )}
      </Card>

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
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-gray-900">{t('page.asset_detail.invite_user')}</h3>
            <p className="mt-2 text-sm text-gray-600">{t('page.asset_detail.invite_modal_desc')}</p>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!inviteEmail.trim()) return;
                inviteAssignableUser.mutate(inviteEmail.trim());
              }}
              className="mt-4 space-y-4"
            >
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">{t('table.email')}</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder={t('common.placeholder_user_email')}
                  required
                  autoFocus
                  className="w-full rounded-lg border px-3 py-2 text-sm"
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setInviteModalOpen(false)}
                  disabled={inviteAssignableUser.isPending}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={inviteAssignableUser.isPending || !inviteEmail.trim()}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
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
