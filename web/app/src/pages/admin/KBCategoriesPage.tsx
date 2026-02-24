import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Tooltip } from '../../components/ui/Tooltip';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { ArticleCategory } from '../../types';

interface EditState {
  id: string;
  name: string;
  description: string;
  sort_order: number;
}

export default function KBCategoriesPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [createOrder, setCreateOrder] = useState(0);
  const [createError, setCreateError] = useState('');

  const [editModal, setEditModal] = useState<EditState | null>(null);
  const [editError, setEditError] = useState('');
  const [pendingDelete, setPendingDelete] = useState<{ id: string; name: string } | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['kb-categories'],
    queryFn: async () => {
      const { data } = await api.get('/kb/categories');
      return data.data as ArticleCategory[];
    },
  });

  const create = useMutation({
    mutationFn: () => api.post('/kb/categories', {
      name: createName.trim(),
      description: createDesc.trim() || null,
      sort_order: createOrder,
    }),
    onSuccess: () => {
      setCreateName(''); setCreateDesc(''); setCreateOrder(0); setCreateError('');
      setCreateOpen(false);
      queryClient.invalidateQueries({ queryKey: ['kb-categories'] });
      showToast({ title: t('page.kb_categories.created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      setCreateError(detail);
    },
  });

  const update = useMutation({
    mutationFn: (s: EditState) => api.put(`/kb/categories/${s.id}`, {
      name: s.name.trim(),
      description: s.description.trim() || null,
      sort_order: s.sort_order,
    }),
    onSuccess: () => {
      setEditModal(null); setEditError('');
      queryClient.invalidateQueries({ queryKey: ['kb-categories'] });
      showToast({ title: t('page.kb_categories.updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      setEditError(detail);
    },
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/kb/categories/${id}`),
    onSuccess: () => {
      setPendingDelete(null);
      queryClient.invalidateQueries({ queryKey: ['kb-categories'] });
      showToast({ title: t('page.kb_categories.deleted'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      showToast({ title: detail, variant: 'error' });
    },
  });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (pendingDelete && !remove.isPending) { setPendingDelete(null); return; }
      if (editModal && !update.isPending) { setEditModal(null); setEditError(''); return; }
      if (createOpen && !create.isPending) { setCreateOpen(false); setCreateName(''); setCreateDesc(''); setCreateOrder(0); setCreateError(''); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [create.isPending, createOpen, remove.isPending, update.isPending, editModal, pendingDelete]);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.kb_categories.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.kb_categories.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={() => { setCreateName(''); setCreateDesc(''); setCreateOrder(0); setCreateError(''); setCreateOpen(true); }}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.kb_categories.new')}
        </button>
      </div>

      {isLoading ? <Card><Loading /></Card> : isError ? (
        <Card><ErrorState message={(error as Error)?.message} onRetry={() => { void refetch(); }} /></Card>
      ) : !data?.length ? (
        <Card>
          <EmptyState
            message={t('page.kb_categories.empty')}
            action={
              <button type="button" onClick={() => setCreateOpen(true)}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90">
                {t('page.kb_categories.new')}
              </button>
            }
          />
        </Card>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>{t('table.name')}</Th>
              <Th>{t('page.kb_categories.description')}</Th>
              <Th>{t('page.kb_categories.sort_order')}</Th>
              <Th>{t('page.kb_categories.articles')}</Th>
              <Th className="text-right">{t('table.actions')}</Th>
            </tr>
          </thead>
          <tbody>
            {data.map((cat) => (
              <Tr key={cat.id}>
                <Td className="font-medium">{cat.name}</Td>
                <Td><span className="text-muted-foreground text-sm">{cat.description || '-'}</span></Td>
                <Td>{cat.sort_order}</Td>
                <Td>{cat.article_count}</Td>
                <Td className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Tooltip content={t('common.edit')}>
                      <button type="button"
                        onClick={() => { setEditError(''); setEditModal({ id: cat.id, name: cat.name, description: cat.description || '', sort_order: cat.sort_order }); }}
                        aria-label={t('common.edit')}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors">
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M15.2 5.2 18.8 8.8" /><path d="M4 20h3.4l10-10a2.5 2.5 0 0 0-3.5-3.5L4 16.5V20z" />
                        </svg>
                      </button>
                    </Tooltip>
                    <Tooltip content={t('common.delete')}>
                      <button type="button"
                        onClick={() => setPendingDelete({ id: cat.id, name: cat.name })}
                        aria-label={t('common.delete')}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-destructive/40 text-destructive hover:bg-destructive/10 transition-colors">
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M3 6h18" /><path d="M8 6V4h8v2" /><path d="M19 6l-1 14H6L5 6" /><path d="M10 11v6M14 11v6" />
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

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={t('page.kb_categories.delete_title')}
        description={pendingDelete ? t('page.kb_categories.delete_desc', { name: pendingDelete.name }) : ''}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={remove.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => { if (pendingDelete) remove.mutate(pendingDelete.id); }}
      />

      {createOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button type="button" className="absolute inset-0 bg-black/40" onClick={() => { if (!create.isPending) { setCreateOpen(false); } }} aria-label={t('common.close')} />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.kb_categories.new')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); if (!createName.trim()) { setCreateError(t('page.kb_categories.error_name_required')); return; } setCreateError(''); create.mutate(); }} className="mt-4 space-y-4">
              {createError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{createError}</div>}
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('table.name')} *</label>
                <input type="text" value={createName} onChange={(e) => setCreateName(e.target.value)} className="w-full bg-card" autoFocus required maxLength={100} />
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.kb_categories.description')}</label>
                <input type="text" value={createDesc} onChange={(e) => setCreateDesc(e.target.value)} className="w-full bg-card" maxLength={300} />
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.kb_categories.sort_order')}</label>
                <input type="number" value={createOrder} onChange={(e) => setCreateOrder(Number(e.target.value))} className="w-full bg-card" />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => { if (!create.isPending) setCreateOpen(false); }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
                  {t('common.cancel')}
                </button>
                <button type="submit" disabled={create.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50">
                  {create.isPending ? t('common.working') : t('common.create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editModal && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button type="button" className="absolute inset-0 bg-black/40" onClick={() => { if (!update.isPending) { setEditModal(null); setEditError(''); } }} aria-label={t('common.close')} />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('common.edit')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); if (!editModal.name.trim()) { setEditError(t('page.kb_categories.error_name_required')); return; } setEditError(''); update.mutate(editModal); }} className="mt-4 space-y-4">
              {editError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{editError}</div>}
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('table.name')} *</label>
                <input type="text" value={editModal.name} onChange={(e) => setEditModal({ ...editModal, name: e.target.value })} className="w-full bg-card" required maxLength={100} />
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.kb_categories.description')}</label>
                <input type="text" value={editModal.description} onChange={(e) => setEditModal({ ...editModal, description: e.target.value })} className="w-full bg-card" maxLength={300} />
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.kb_categories.sort_order')}</label>
                <input type="number" value={editModal.sort_order} onChange={(e) => setEditModal({ ...editModal, sort_order: Number(e.target.value) })} className="w-full bg-card" />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => { if (!update.isPending) { setEditModal(null); setEditError(''); } }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
                  {t('common.cancel')}
                </button>
                <button type="submit" disabled={update.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50">
                  {update.isPending ? t('common.working') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
