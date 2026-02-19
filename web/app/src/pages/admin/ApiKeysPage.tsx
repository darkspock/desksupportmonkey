import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { ApiKey, CreatedApiKey } from '../../types';

export default function ApiKeysPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [showForm, setShowForm] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [formError, setFormError] = useState('');
  const [rawKey, setRawKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [pendingRevoke, setPendingRevoke] = useState<{ id: string; name: string } | null>(null);

  const { data: keys, isLoading, isError, error: listError, refetch } = useQuery({
    queryKey: ['api-keys'],
    queryFn: async () => {
      const { data } = await api.get('/auth/api-keys');
      return (data as { data: ApiKey[] }).data;
    },
  });

  const activeCount = keys?.filter((k) => k.is_active).length ?? 0;
  const canCreate = activeCount < 10;

  const create = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/auth/api-keys', { name: keyName });
      return (data as { data: CreatedApiKey }).data;
    },
    onSuccess: (data) => {
      setRawKey(data.raw_key);
      setKeyName('');
      setShowForm(false);
      setFormError('');
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      showToast({ title: t('page.api_keys.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.api_keys.error_generic');
      setFormError(detail);
      showToast({ title: t('page.api_keys.error_create_title'), description: detail, variant: 'error' });
    },
  });

  const revoke = useMutation({
    mutationFn: (id: string) => api.delete(`/auth/api-keys/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      setPendingRevoke(null);
      showToast({ title: t('page.api_keys.toast_revoked'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.api_keys.error_generic');
      showToast({ title: t('page.api_keys.error_revoke_title'), description: detail, variant: 'error' });
    },
  });

  const copyToClipboard = async () => {
    if (!rawKey) return;
    try {
      await navigator.clipboard.writeText(rawKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      showToast({ title: t('page.api_keys.error_copy'), variant: 'error' });
    }
  };

  const closeKeyModal = () => {
    setRawKey(null);
    setCopied(false);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.api_keys.title')}</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          disabled={!canCreate && !showForm}
          className={showForm
            ? 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50'
            : 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50'}
        >
          {showForm ? t('common.close') : t('page.api_keys.create_button')}
        </button>
      </div>

      {!canCreate && !showForm && (
        <div className="mb-4 rounded-lg border border-warning/20 bg-warning/10 px-4 py-3 text-sm text-warning">
          {t('page.api_keys.key_limit_reached')}
        </div>
      )}

      {showForm && (
        <Card className="mb-4">
          <form
            onSubmit={(e) => { e.preventDefault(); create.mutate(); }}
            className="flex gap-3 items-end"
          >
            <div className="flex-1">
              {formError && <p className="text-sm text-destructive mb-2">{formError}</p>}
              <label className="block mb-1.5 text-muted-foreground">
                {t('page.api_keys.name_label')}
              </label>
              <input
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                placeholder={t('page.api_keys.name_placeholder')}
                required
                maxLength={100}
                className="w-full bg-card"
              />
            </div>
            <button
              type="submit"
              disabled={create.isPending || !keyName.trim()}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {create.isPending ? t('page.api_keys.creating') : t('common.create')}
            </button>
          </form>
        </Card>
      )}

      <Card>
        {isLoading ? <Loading /> : isError ? (
          <ErrorState
            message={(listError as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.api_keys.error_load')}
            onRetry={() => { void refetch(); }}
          />
        ) : !keys?.length ? (
          <EmptyState message={t('page.api_keys.empty')} />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>{t('table.name')}</Th>
                <Th>{t('page.api_keys.created')}</Th>
                <Th>{t('page.api_keys.last_used')}</Th>
                <Th>{t('table.status')}</Th>
                <Th>{t('table.actions')}</Th>
              </tr>
            </thead>
            <tbody>
              {keys.map((key) => (
                <tr key={key.id}>
                  <Td>{key.name}</Td>
                  <Td>{formatDate(key.created_at)}</Td>
                  <Td>{key.last_used_at ? formatDate(key.last_used_at) : t('page.api_keys.never')}</Td>
                  <Td>
                    <Badge variant={key.is_active ? 'success' : 'danger'}>
                      {key.is_active ? t('page.api_keys.active') : t('page.api_keys.revoked')}
                    </Badge>
                  </Td>
                  <Td>
                    {key.is_active && (
                      <button
                        onClick={() => setPendingRevoke({ id: key.id, name: key.name })}
                        className="text-xs text-destructive hover:underline"
                      >
                        {t('page.api_keys.revoke')}
                      </button>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      {/* Revoke confirmation dialog */}
      <ConfirmDialog
        open={Boolean(pendingRevoke)}
        title={t('page.api_keys.revoke_confirm_title')}
        description={pendingRevoke ? t('page.api_keys.revoke_confirm_desc', { name: pendingRevoke.name }) : ''}
        confirmLabel={t('page.api_keys.revoke')}
        tone="danger"
        busy={revoke.isPending}
        onCancel={() => setPendingRevoke(null)}
        onConfirm={() => {
          if (pendingRevoke) {
            revoke.mutate(pendingRevoke.id);
          }
        }}
      />

      {/* Raw key display modal */}
      {rawKey && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={closeKeyModal}
            aria-label={t('common.close')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">
              {t('page.api_keys.create_modal_title')}
            </h3>
            <div className="mt-4 rounded-lg bg-secondary border border-border p-3 font-mono text-sm break-all select-all">
              {rawKey}
            </div>
            <div className="mt-3 rounded-lg border border-warning/20 bg-warning/10 px-3 py-2 text-sm text-warning">
              {t('page.api_keys.create_modal_warning')}
            </div>
            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={copyToClipboard}
                className="flex-1 inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {copied ? t('page.api_keys.copied') : t('page.api_keys.copy_button')}
              </button>
              <button
                type="button"
                onClick={closeKeyModal}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
              >
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
