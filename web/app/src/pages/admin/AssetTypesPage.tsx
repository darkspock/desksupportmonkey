import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { StatusBadge } from '../../components/ui/Badge';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Tooltip } from '../../components/ui/Tooltip';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { AssetTypeDefinition } from '../../types';

interface TypeForm {
  name: string;
  icon: string;
}

function emptyForm(): TypeForm {
  return { name: '', icon: '' };
}

export default function AssetTypesPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [createModal, setCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<TypeForm>(emptyForm());
  const [createError, setCreateError] = useState('');

  const [editModal, setEditModal] = useState<AssetTypeDefinition | null>(null);
  const [editForm, setEditForm] = useState<TypeForm>(emptyForm());
  const [editError, setEditError] = useState('');

  const [pendingDelete, setPendingDelete] = useState<AssetTypeDefinition | null>(null);
  const [pendingToggle, setPendingToggle] = useState<AssetTypeDefinition | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['asset-types'],
    queryFn: async () => {
      const { data } = await api.get('/asset-types');
      return data.data as AssetTypeDefinition[];
    },
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['asset-types'] });

  const createType = useMutation({
    mutationFn: () => api.post('/asset-types', {
      name: createForm.name.trim(),
      icon: createForm.icon.trim() || null,
    }),
    onSuccess: () => {
      invalidate();
      setCreateModal(false);
      setCreateForm(emptyForm());
      setCreateError('');
      showToast({ title: t('page.asset_types.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      setCreateError(detail);
      showToast({ title: detail, variant: 'error' });
    },
  });

  const updateType = useMutation({
    mutationFn: () => {
      if (!editModal) return Promise.reject();
      return api.put(`/asset-types/${editModal.id}`, {
        name: editForm.name.trim(),
        icon: editForm.icon.trim() || null,
      });
    },
    onSuccess: () => {
      invalidate();
      setEditModal(null);
      setEditForm(emptyForm());
      setEditError('');
      showToast({ title: t('page.asset_types.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      setEditError(detail);
      showToast({ title: detail, variant: 'error' });
    },
  });

  const toggleActive = useMutation({
    mutationFn: (at: AssetTypeDefinition) =>
      api.put(`/asset-types/${at.id}`, { is_active: !at.is_active }),
    onSuccess: () => {
      invalidate();
      setPendingToggle(null);
      showToast({ title: t('page.asset_types.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      showToast({ title: detail, variant: 'error' });
    },
  });

  const deleteType = useMutation({
    mutationFn: (id: string) => api.delete(`/asset-types/${id}`),
    onSuccess: () => {
      invalidate();
      setPendingDelete(null);
      showToast({ title: t('page.asset_types.toast_deleted'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      showToast({ title: detail, variant: 'error' });
    },
  });

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (pendingDelete && !deleteType.isPending) { setPendingDelete(null); return; }
      if (pendingToggle && !toggleActive.isPending) { setPendingToggle(null); return; }
      if (editModal && !updateType.isPending) { setEditModal(null); setEditError(''); return; }
      if (createModal && !createType.isPending) { setCreateModal(false); setCreateError(''); }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [createModal, createType.isPending, deleteType.isPending, editModal, pendingDelete, pendingToggle, toggleActive.isPending, updateType.isPending]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.asset_types.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.asset_types.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={() => { setCreateError(''); setCreateForm(emptyForm()); setCreateModal(true); }}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.asset_types.new')}
        </button>
      </div>

      {isLoading ? <Card><Loading /></Card> : isError ? (
        <Card>
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => { void refetch(); }}
          />
        </Card>
      ) : !data?.length ? (
        <Card>
          <EmptyState
            message={t('page.asset_types.empty')}
            action={(
              <button
                type="button"
                onClick={() => { setCreateError(''); setCreateForm(emptyForm()); setCreateModal(true); }}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
              >
                {t('page.asset_types.new')}
              </button>
            )}
          />
        </Card>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>{t('table.name')}</Th>
              <Th>{t('page.asset_types.code')}</Th>
              <Th>{t('page.asset_types.icon')}</Th>
              <Th>{t('table.status')}</Th>
              <Th className="text-right">{t('table.actions')}</Th>
            </tr>
          </thead>
          <tbody>
            {data.map((at) => (
              <Tr key={at.id}>
                <Td className="font-medium">{at.name}</Td>
                <Td><code className="text-xs bg-muted px-1.5 py-0.5 rounded">{at.code}</code></Td>
                <Td>{at.icon || '—'}</Td>
                <Td><StatusBadge status={at.is_active ? 'active' : 'deactivated'} /></Td>
                <Td className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Tooltip content={t('common.edit')}>
                      <button
                        type="button"
                        onClick={() => {
                          setEditError('');
                          setEditForm({ name: at.name, icon: at.icon ?? '' });
                          setEditModal(at);
                        }}
                        aria-label={t('common.edit')}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                      >
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M15.2 5.2 18.8 8.8" />
                          <path d="M4 20h3.4l10-10a2.5 2.5 0 0 0-3.5-3.5L4 16.5V20z" />
                        </svg>
                      </button>
                    </Tooltip>
                    <Tooltip content={at.is_active ? t('page.asset_types.deactivate') : t('page.asset_types.activate')}>
                      <button
                        type="button"
                        onClick={() => setPendingToggle(at)}
                        aria-label={at.is_active ? t('page.asset_types.deactivate') : t('page.asset_types.activate')}
                        className={`inline-flex h-8 w-8 items-center justify-center rounded-md border transition-colors ${at.is_active ? 'border-warning/40 text-warning hover:bg-warning/10' : 'border-success/40 text-success hover:bg-success/10'}`}
                      >
                        {at.is_active ? (
                          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18.36 6.64A9 9 0 0 1 20.77 15" />
                            <path d="M6.16 6.16a9 9 0 1 0 12.68 12.68" />
                            <line x1="2" y1="2" x2="22" y2="22" />
                          </svg>
                        ) : (
                          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                            <polyline points="22 4 12 14.01 9 11.01" />
                          </svg>
                        )}
                      </button>
                    </Tooltip>
                    <Tooltip content={t('common.delete')}>
                      <button
                        type="button"
                        onClick={() => setPendingDelete(at)}
                        aria-label={t('common.delete')}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-destructive/40 text-destructive hover:bg-destructive/10 transition-colors"
                      >
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M3 6h18" />
                          <path d="M8 6V4h8v2" />
                          <path d="M19 6l-1 14H6L5 6" />
                          <path d="M10 11v6M14 11v6" />
                        </svg>
                      </button>
                    </Tooltip>
                  </div>
                </Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      )}

      {/* Delete confirm */}
      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={t('page.asset_types.delete_title')}
        description={t('page.asset_types.delete_desc', { name: pendingDelete?.name ?? '' })}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={deleteType.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => { if (pendingDelete) deleteType.mutate(pendingDelete.id); }}
      />

      {/* Toggle confirm */}
      <ConfirmDialog
        open={Boolean(pendingToggle)}
        title={pendingToggle?.is_active ? t('page.asset_types.deactivate') : t('page.asset_types.activate')}
        description={t('page.asset_types.toggle_desc')}
        confirmLabel={pendingToggle?.is_active ? t('page.asset_types.deactivate') : t('page.asset_types.activate')}
        tone={pendingToggle?.is_active ? 'danger' : 'default'}
        busy={toggleActive.isPending}
        onCancel={() => setPendingToggle(null)}
        onConfirm={() => { if (pendingToggle) toggleActive.mutate(pendingToggle); }}
      />

      {/* Create modal */}
      {createModal && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => { if (!createType.isPending) { setCreateModal(false); setCreateError(''); } }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.asset_types.new')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!createForm.name.trim()) { setCreateError(t('page.asset_types.name_required')); return; }
                setCreateError('');
                createType.mutate();
              }}
              className="mt-4 space-y-4"
            >
              {createError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{createError}</div>}
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('table.name')}</label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  placeholder={t('page.asset_types.name_placeholder')}
                  className="w-full bg-card"
                  autoFocus
                  required
                />
              </div>
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.asset_types.icon')}</label>
                <input
                  type="text"
                  value={createForm.icon}
                  onChange={(e) => setCreateForm({ ...createForm, icon: e.target.value })}
                  placeholder={t('page.asset_types.icon_placeholder')}
                  className="w-full bg-card"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { if (!createType.isPending) { setCreateModal(false); setCreateError(''); } }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={createType.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {createType.isPending ? t('common.working') : t('common.create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit modal */}
      {editModal && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => { if (!updateType.isPending) { setEditModal(null); setEditError(''); } }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('common.edit')}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{t('page.asset_types.code')}: <code>{editModal.code}</code></p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!editForm.name.trim()) { setEditError(t('page.asset_types.name_required')); return; }
                setEditError('');
                updateType.mutate();
              }}
              className="mt-4 space-y-4"
            >
              {editError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{editError}</div>}
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('table.name')}</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full bg-card"
                  autoFocus
                  required
                />
              </div>
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.asset_types.icon')}</label>
                <input
                  type="text"
                  value={editForm.icon}
                  onChange={(e) => setEditForm({ ...editForm, icon: e.target.value })}
                  placeholder={t('page.asset_types.icon_placeholder')}
                  className="w-full bg-card"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { if (!updateType.isPending) { setEditModal(null); setEditError(''); } }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={updateType.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {updateType.isPending ? t('common.working') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
