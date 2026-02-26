import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge, Badge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';
import { formatDateTime } from '../../lib/date';
import type { Asset, MyCustody, MyCustodyHistoryItem, PaginationMeta } from '../../types';

type Tab = 'current' | 'history';

export default function MyEquipmentPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [tab, setTab] = useState<Tab>('current');
  const [historyPage, setHistoryPage] = useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['my-equipment'],
    queryFn: async () => {
      const { data } = await api.get('/my/equipment');
      return data.data as Asset[];
    },
  });

  const { data: custody, isLoading: custodyLoading } = useQuery({
    queryKey: ['my-custody'],
    queryFn: async () => {
      const { data } = await api.get('/my/custody');
      return data.data as MyCustody;
    },
  });

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['my-custody-history', historyPage],
    queryFn: async () => {
      const { data } = await api.get('/my/custody/history', { params: { page: historyPage, page_size: 20 } });
      return data as { data: MyCustodyHistoryItem[]; meta: PaginationMeta };
    },
    enabled: tab === 'history',
  });

  const acceptMutation = useMutation({
    mutationFn: async (assetId: string) => {
      await api.post(`/my/equipment/${assetId}/accept`);
    },
    onSuccess: () => {
      toast({ title: t('page.my_equipment.accept_success'), variant: 'success' });
      void queryClient.invalidateQueries({ queryKey: ['my-custody'] });
      void queryClient.invalidateQueries({ queryKey: ['my-equipment'] });
      void queryClient.invalidateQueries({ queryKey: ['my-custody-history'] });
    },
    onError: () => {
      toast({ title: t('page.my_equipment.accept_error'), variant: 'destructive' });
    },
  });

  const pendingItems = custody?.pending_acceptance ?? [];
  const history = historyData?.data ?? [];
  const historyMeta = historyData?.meta;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.my_equipment.title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.my_equipment.subtitle')}</p>
      </div>

      {/* Pending acceptance banner */}
      {!custodyLoading && pendingItems.length > 0 && (
        <Card className="border-amber-200 bg-amber-50 dark:bg-amber-950/20 dark:border-amber-800">
          <div className="flex items-start gap-3">
            <svg viewBox="0 0 24 24" className="h-5 w-5 shrink-0 text-amber-600 mt-0.5" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
            </svg>
            <div className="flex-1 space-y-3">
              <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                {t('page.my_equipment.pending_acceptance', { count: pendingItems.length })}
              </p>
              {pendingItems.map((item) => (
                <div key={item.checkout_id} className="flex items-center justify-between rounded-md border border-amber-200 dark:border-amber-800 bg-white dark:bg-amber-950/40 px-3 py-2">
                  <div className="text-sm">
                    <span className="font-medium text-foreground">{item.asset_id}</span>
                    <span className="mx-2 text-muted-foreground">|</span>
                    <span className="text-muted-foreground">{t('page.my_equipment.condition')}: {t(`enum.${item.condition_out}`)}</span>
                    <span className="mx-2 text-muted-foreground">|</span>
                    <span className="text-muted-foreground">{formatDateTime(item.checked_out_at)}</span>
                  </div>
                  <button
                    type="button"
                    disabled={acceptMutation.isPending}
                    onClick={() => acceptMutation.mutate(item.asset_id)}
                    className="inline-flex items-center justify-center gap-1.5 rounded-md h-8 px-3 text-xs font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                  >
                    {t('page.my_equipment.confirm_receipt')}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        {(['current', 'history'] as const).map((t_) => (
          <button
            key={t_}
            type="button"
            onClick={() => { setTab(t_); if (t_ === 'history') setHistoryPage(1); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t_
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            {t(`page.my_equipment.tab_${t_}`)}
          </button>
        ))}
      </div>

      {/* Current equipment table */}
      {tab === 'current' && (
        <Card className="overflow-hidden p-0">
          {isLoading ? (
            <div className="p-5"><Loading /></div>
          ) : isError ? (
            <div className="p-5">
              <ErrorState
                message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
                onRetry={() => { void refetch(); }}
              />
            </div>
          ) : !data?.length ? (
            <div className="p-5">
              <EmptyState
                message={t('page.my_equipment.empty')}
                action={(
                  <Link
                    to="/my/requests/new"
                    className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                  >
                    {t('page.my_equipment.request_cta')}
                  </Link>
                )}
              />
            </div>
          ) : (
            <Table>
              <thead>
                <tr className="hover:bg-transparent">
                  <Th className="pl-4">{t('table.type')}</Th>
                  <Th>{t('table.brand')}</Th>
                  <Th>{t('table.model')}</Th>
                  <Th>{t('table.serial_number')}</Th>
                  <Th>{t('table.status')}</Th>
                </tr>
              </thead>
              <tbody>
                {data.map((a) => (
                  <Tr key={a.id}>
                    <Td className="pl-4">{t(`enum.${a.type}`)}</Td>
                    <Td>{a.brand}</Td>
                    <Td>{a.model}</Td>
                    <Td><span className="font-mono text-xs">{a.serial_number}</span></Td>
                    <Td><StatusBadge status={a.status} /></Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      )}

      {/* History table */}
      {tab === 'history' && (
        <Card className="overflow-hidden p-0">
          {historyLoading ? (
            <div className="p-5"><Loading /></div>
          ) : !history.length ? (
            <div className="p-5">
              <EmptyState message={t('page.my_equipment.history_empty')} />
            </div>
          ) : (
            <>
              <Table>
                <thead>
                  <tr className="hover:bg-transparent">
                    <Th className="pl-4">{t('table.type')}</Th>
                    <Th>{t('table.brand')}</Th>
                    <Th>{t('table.model')}</Th>
                    <Th>{t('page.my_equipment.condition')}</Th>
                    <Th>{t('table.status')}</Th>
                    <Th>{t('page.my_equipment.date_range')}</Th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <Tr key={h.checkout_id}>
                      <Td className="pl-4">{h.asset_type ? t(`enum.${h.asset_type}`) : '—'}</Td>
                      <Td>{h.asset_brand ?? '—'}</Td>
                      <Td>{h.asset_model ?? '—'}</Td>
                      <Td>
                        {h.condition_in ? t(`enum.${h.condition_in}`) : h.condition_out ? t(`enum.${h.condition_out}`) : '—'}
                      </Td>
                      <Td>
                        <Badge variant={h.cancelled_at ? 'danger' : 'success'}>
                          {h.cancelled_at ? t('page.my_equipment.cancelled') : t('page.my_equipment.checked_in')}
                        </Badge>
                      </Td>
                      <Td className="text-muted-foreground text-xs whitespace-nowrap">
                        {formatDateTime(h.checked_out_at)}
                        <span className="mx-1">→</span>
                        {formatDateTime(h.checked_in_at ?? h.cancelled_at ?? '')}
                      </Td>
                    </Tr>
                  ))}
                </tbody>
              </Table>
              {historyMeta && historyMeta.total > historyMeta.page_size && (
                <div className="flex items-center justify-between border-t border-border px-4 py-3">
                  <p className="text-xs text-muted-foreground">
                    {historyMeta.total} {historyMeta.total === 1 ? 'record' : 'records'}
                  </p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      disabled={historyPage <= 1}
                      onClick={() => setHistoryPage((p) => p - 1)}
                      className="rounded-md h-8 px-3 text-xs font-medium border border-border bg-background text-foreground hover:bg-accent disabled:opacity-50 disabled:pointer-events-none"
                    >
                      &larr;
                    </button>
                    <button
                      type="button"
                      disabled={historyPage * historyMeta.page_size >= historyMeta.total}
                      onClick={() => setHistoryPage((p) => p + 1)}
                      className="rounded-md h-8 px-3 text-xs font-medium border border-border bg-background text-foreground hover:bg-accent disabled:opacity-50 disabled:pointer-events-none"
                    >
                      &rarr;
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </Card>
      )}
    </div>
  );
}
