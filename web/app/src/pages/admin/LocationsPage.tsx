import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Pencil } from 'lucide-react';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Tooltip } from '../../components/ui/Tooltip';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { AssetLocation } from '../../types';

interface LocationFormFields {
  name: string;
  inUse: boolean;
  street_line_1: string;
  street_line_2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone: string;
}

interface EditModalState extends LocationFormFields {
  locationId: string;
  isSystem: boolean;
}

const EMPTY_FORM: LocationFormFields = {
  name: '',
  inUse: true,
  street_line_1: '',
  street_line_2: '',
  city: '',
  state: '',
  postal_code: '',
  country: '',
  phone: '',
};

export default function LocationsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState<LocationFormFields>(EMPTY_FORM);
  const [createError, setCreateError] = useState('');
  const [editModal, setEditModal] = useState<EditModalState | null>(null);
  const [editError, setEditError] = useState('');
  const [pendingDelete, setPendingDelete] = useState<{ id: string; name: string } | null>(null);

  const { data: locations, isLoading, isError, error: listError, refetch } = useQuery({
    queryKey: ['locations'],
    queryFn: async () => {
      const { data } = await api.get('/assets/locations');
      return data.data as AssetLocation[];
    },
  });

  const create = useMutation({
    mutationFn: (form: LocationFormFields) => api.post('/assets/locations', {
      name: form.name.trim(),
      in_use: form.inUse,
      street_line_1: form.street_line_1 || null,
      street_line_2: form.street_line_2 || null,
      city: form.city || null,
      state: form.state || null,
      postal_code: form.postal_code || null,
      country: form.country || null,
      phone: form.phone || null,
    }),
    onSuccess: () => {
      setCreateForm(EMPTY_FORM);
      setCreateError('');
      setCreateModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['locations'] });
      showToast({ title: t('page.locations.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.locations.error_generic');
      setCreateError(detail);
      showToast({ title: t('page.locations.error_create_title'), description: detail, variant: 'error' });
    },
  });

  const saveEdit = useMutation({
    mutationFn: async (payload: EditModalState) => {
      await api.put(`/assets/locations/${payload.locationId}`, {
        name: payload.name.trim(),
        in_use: payload.inUse,
        street_line_1: payload.street_line_1 || null,
        street_line_2: payload.street_line_2 || null,
        city: payload.city || null,
        state: payload.state || null,
        postal_code: payload.postal_code || null,
        country: payload.country || null,
        phone: payload.phone || null,
      });
    },
    onSuccess: () => {
      setEditModal(null);
      setEditError('');
      queryClient.invalidateQueries({ queryKey: ['locations'] });
      showToast({ title: t('page.locations.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.locations.error_update');
      setEditError(detail);
      showToast({ title: t('page.locations.error_update_title'), description: detail, variant: 'error' });
    },
  });

  const deleteLocation = useMutation({
    mutationFn: (id: string) => api.delete(`/assets/locations/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] });
      setPendingDelete(null);
      showToast({ title: t('page.locations.toast_deleted'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.locations.error_delete');
      showToast({ title: t('page.locations.error_delete_title'), description: detail, variant: 'error' });
    },
  });

  const toggleInUse = useMutation({
    mutationFn: async ({ id, name, inUse }: { id: string; name: string; inUse: boolean }) => {
      await api.put(`/assets/locations/${id}`, { name, in_use: inUse });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] });
      showToast({ title: t('page.locations.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.locations.error_update');
      showToast({ title: t('page.locations.error_update_title'), description: detail, variant: 'error' });
    },
  });

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (pendingDelete && !deleteLocation.isPending) {
        setPendingDelete(null);
        return;
      }
      if (editModal && !saveEdit.isPending) {
        setEditModal(null);
        setEditError('');
        return;
      }
      if (createModalOpen && !create.isPending) {
        setCreateModalOpen(false);
        setCreateForm(EMPTY_FORM);
        setCreateError('');
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [create.isPending, createModalOpen, deleteLocation.isPending, editModal, pendingDelete, saveEdit.isPending]);

  const systemLocationLabel = (key: string | null): string => {
    if (!key) return '';
    const map: Record<string, string> = {
      employee: t('page.locations.system_employee'),
      in_transit: t('page.locations.system_in_transit'),
      main_warehouse: t('page.locations.system_warehouse'),
    };
    return map[key] || key;
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.locations.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.locations.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setCreateForm(EMPTY_FORM);
            setCreateError('');
            setCreateModalOpen(true);
          }}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.locations.new')}
        </button>
      </div>

      {isLoading ? <Card><Loading /></Card> : isError ? (
        <Card>
          <ErrorState
            message={(listError as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => { void refetch(); }}
          />
        </Card>
      ) : !locations?.length ? (
        <Card>
          <EmptyState
            message={t('page.locations.empty')}
            action={(
              <button
                type="button"
                onClick={() => {
                  setCreateForm(EMPTY_FORM);
                  setCreateError('');
                  setCreateModalOpen(true);
                }}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
              >
                {t('page.locations.new')}
              </button>
            )}
          />
        </Card>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>{t('table.name')}</Th>
              <Th>{t('table.type')}</Th>
              <Th>{t('page.locations.in_use')}</Th>
              <Th>{t('page.locations.asset_count')}</Th>
              <Th className="text-right">{t('table.actions')}</Th>
            </tr>
          </thead>
          <tbody>
            {locations.map((loc) => (
              <Tr key={loc.id}>
                <Td>
                  <span className="text-sm font-medium text-foreground">{loc.name}</span>
                  {loc.is_system && loc.system_key && (
                    <span className="ml-2 text-xs text-muted-foreground">({systemLocationLabel(loc.system_key)})</span>
                  )}
                  {loc.city && (
                    <span className="block text-xs text-muted-foreground">{[loc.city, loc.state, loc.country].filter(Boolean).join(', ')}</span>
                  )}
                </Td>
                <Td>
                  {loc.is_system ? (
                    <Badge variant="secondary">
                      <svg viewBox="0 0 24 24" className="mr-1 h-3 w-3 inline" fill="none" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                      </svg>
                      {t('page.locations.system')}
                    </Badge>
                  ) : (
                    <Badge variant="default">{t('page.locations.custom')}</Badge>
                  )}
                </Td>
                <Td>
                  <label className="relative inline-flex cursor-pointer items-center">
                    <input
                      type="checkbox"
                      checked={loc.in_use}
                      disabled={loc.is_system || toggleInUse.isPending}
                      onChange={() => {
                        if (!loc.is_system) {
                          toggleInUse.mutate({ id: loc.id, name: loc.name, inUse: !loc.in_use });
                        }
                      }}
                      className="peer sr-only"
                    />
                    <div className={`h-5 w-9 rounded-full ${loc.is_system ? 'bg-primary/60 cursor-not-allowed' : 'bg-muted peer-checked:bg-primary'} peer-focus:ring-2 peer-focus:ring-primary/50 after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full`} />
                  </label>
                </Td>
                <Td>
                  <span className="text-sm text-muted-foreground">{loc.asset_count}</span>
                </Td>
                <Td className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Tooltip content={t('common.edit')}>
                      <button
                        type="button"
                        onClick={() => {
                          setEditError('');
                          setEditModal({
                            locationId: loc.id,
                            isSystem: loc.is_system,
                            name: loc.name,
                            inUse: loc.in_use,
                            street_line_1: loc.street_line_1 ?? '',
                            street_line_2: loc.street_line_2 ?? '',
                            city: loc.city ?? '',
                            state: loc.state ?? '',
                            postal_code: loc.postal_code ?? '',
                            country: loc.country ?? '',
                            phone: loc.phone ?? '',
                          });
                        }}
                        aria-label={t('common.edit')}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                    </Tooltip>
                    {!loc.is_system && (
                      <Tooltip content={loc.asset_count > 0 ? t('page.locations.delete_has_assets') : t('common.delete')}>
                        <button
                          type="button"
                          onClick={() => setPendingDelete({ id: loc.id, name: loc.name })}
                          disabled={loc.asset_count > 0}
                          aria-label={t('common.delete')}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-destructive/40 text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 6h18" />
                            <path d="M8 6V4h8v2" />
                            <path d="M19 6l-1 14H6L5 6" />
                            <path d="M10 11v6M14 11v6" />
                          </svg>
                        </button>
                      </Tooltip>
                    )}
                  </div>
                </Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      )}

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={t('page.locations.delete_title')}
        description={pendingDelete ? t('page.locations.delete_desc', { name: pendingDelete.name }) : ''}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={deleteLocation.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete) deleteLocation.mutate(pendingDelete.id);
        }}
      />

      {createModalOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (create.isPending) return;
              setCreateModalOpen(false);
              setCreateForm(EMPTY_FORM);
              setCreateError('');
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.locations.new')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!createForm.name.trim()) {
                  setCreateError(t('page.locations.error_name_required'));
                  return;
                }
                setCreateError('');
                create.mutate(createForm);
              }}
              className="mt-4 space-y-4"
            >
              <div>
                {createError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{createError}</div>}
                <label className="mb-1.5 block text-muted-foreground">{t('table.name')}</label>
                <input type="text" value={createForm.name} onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })} placeholder={t('page.locations.name_placeholder')} className="w-full bg-card" autoFocus required />
              </div>
              <div className="border-t border-border pt-3">
                <p className="mb-2 text-sm font-medium text-muted-foreground">{t('page.locations.address')}</p>
                <div className="space-y-2">
                  <input type="text" value={createForm.street_line_1} onChange={(e) => setCreateForm({ ...createForm, street_line_1: e.target.value })} placeholder={t('page.locations.street_line_1')} className="w-full bg-card" />
                  <input type="text" value={createForm.street_line_2} onChange={(e) => setCreateForm({ ...createForm, street_line_2: e.target.value })} placeholder={t('page.locations.street_line_2')} className="w-full bg-card" />
                  <div className="grid grid-cols-2 gap-2">
                    <input type="text" value={createForm.city} onChange={(e) => setCreateForm({ ...createForm, city: e.target.value })} placeholder={t('page.locations.city')} className="w-full bg-card" />
                    <input type="text" value={createForm.state} onChange={(e) => setCreateForm({ ...createForm, state: e.target.value })} placeholder={t('page.locations.state')} className="w-full bg-card" />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <input type="text" value={createForm.postal_code} onChange={(e) => setCreateForm({ ...createForm, postal_code: e.target.value })} placeholder={t('page.locations.postal_code')} className="w-full bg-card" />
                    <input type="text" value={createForm.country} onChange={(e) => setCreateForm({ ...createForm, country: e.target.value })} placeholder={t('page.locations.country')} className="w-full bg-card" />
                  </div>
                  <input type="text" value={createForm.phone} onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })} placeholder={t('page.locations.phone')} className="w-full bg-card" />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => { if (create.isPending) return; setCreateModalOpen(false); setCreateForm(EMPTY_FORM); setCreateError(''); }} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
                  {t('common.cancel')}
                </button>
                <button type="submit" disabled={create.isPending} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50">
                  {create.isPending ? t('common.working') : t('common.create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editModal && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (saveEdit.isPending) return;
              setEditModal(null);
              setEditError('');
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.locations.edit_title')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!editModal.name.trim()) {
                  setEditError(t('page.locations.error_name_required'));
                  return;
                }
                setEditError('');
                saveEdit.mutate(editModal);
              }}
              className="mt-4 space-y-4"
            >
              <div>
                {editError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{editError}</div>}
                <label className="mb-1.5 block text-muted-foreground">{t('table.name')}</label>
                <input type="text" value={editModal.name} onChange={(e) => setEditModal({ ...editModal, name: e.target.value })} className="w-full bg-card" required disabled={editModal.isSystem} />
              </div>
              {!editModal.isSystem && (
              <div className="flex items-center gap-3">
                <label className="relative inline-flex cursor-pointer items-center">
                  <input type="checkbox" checked={editModal.inUse} onChange={(e) => setEditModal({ ...editModal, inUse: e.target.checked })} className="peer sr-only" />
                  <div className="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary peer-focus:ring-2 peer-focus:ring-primary/50 after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full" />
                </label>
                <div>
                  <span className="text-sm text-foreground">{t('page.locations.in_use')}</span>
                  <p className="text-xs text-muted-foreground">{t('page.locations.in_use_help')}</p>
                </div>
              </div>
              )}
              <div className="border-t border-border pt-3">
                <p className="mb-2 text-sm font-medium text-muted-foreground">{t('page.locations.address')}</p>
                <div className="space-y-2">
                  <input type="text" value={editModal.street_line_1} onChange={(e) => setEditModal({ ...editModal, street_line_1: e.target.value })} placeholder={t('page.locations.street_line_1')} className="w-full bg-card" />
                  <input type="text" value={editModal.street_line_2} onChange={(e) => setEditModal({ ...editModal, street_line_2: e.target.value })} placeholder={t('page.locations.street_line_2')} className="w-full bg-card" />
                  <div className="grid grid-cols-2 gap-2">
                    <input type="text" value={editModal.city} onChange={(e) => setEditModal({ ...editModal, city: e.target.value })} placeholder={t('page.locations.city')} className="w-full bg-card" />
                    <input type="text" value={editModal.state} onChange={(e) => setEditModal({ ...editModal, state: e.target.value })} placeholder={t('page.locations.state')} className="w-full bg-card" />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <input type="text" value={editModal.postal_code} onChange={(e) => setEditModal({ ...editModal, postal_code: e.target.value })} placeholder={t('page.locations.postal_code')} className="w-full bg-card" />
                    <input type="text" value={editModal.country} onChange={(e) => setEditModal({ ...editModal, country: e.target.value })} placeholder={t('page.locations.country')} className="w-full bg-card" />
                  </div>
                  <input type="text" value={editModal.phone} onChange={(e) => setEditModal({ ...editModal, phone: e.target.value })} placeholder={t('page.locations.phone')} className="w-full bg-card" />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => { if (saveEdit.isPending) return; setEditModal(null); setEditError(''); }} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
                  {t('common.cancel')}
                </button>
                <button type="submit" disabled={saveEdit.isPending} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50">
                  {saveEdit.isPending ? t('common.working') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
