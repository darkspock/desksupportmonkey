import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Badge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { ErrorState } from '../../components/ui/StateBlock';
import { formatDate, formatDateTime } from '../../lib/date';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import { useAuth } from '../../contexts/AuthContext';
import type { PurchaseOrder, PurchaseOrderStatus, PurchaseOrderItem, Department } from '../../types';

const STATUS_VARIANT: Record<string, 'default' | 'info' | 'warning' | 'success' | 'danger'> = {
  DRAFT: 'default',
  SUBMITTED: 'info',
  APPROVED: 'success',
  ORDERED: 'info',
  PARTIALLY_RECEIVED: 'warning',
  RECEIVED: 'success',
  CLOSED: 'default',
  CANCELLED: 'danger',
};

function formatCents(cents: number, currency: string): string {
  return `${currency} ${(cents / 100).toFixed(2)}`;
}

const STATUS_FLOW: PurchaseOrderStatus[] = [
  'DRAFT', 'SUBMITTED', 'APPROVED', 'ORDERED',
  'PARTIALLY_RECEIVED', 'RECEIVED', 'CLOSED',
];

interface ReceiveInput {
  item_id: string;
  received_quantity: number;
  create_asset: boolean;
}

export default function PurchaseOrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { t } = useI18n();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  const [rejectReason, setRejectReason] = useState('');
  const [cancelReason, setCancelReason] = useState('');
  const [showReject, setShowReject] = useState(false);
  const [showCancel, setShowCancel] = useState(false);
  const [receiveQtys, setReceiveQtys] = useState<Record<string, number>>({});
  const [createAssets, setCreateAssets] = useState<Record<string, boolean>>({});
  const [pdfLoading, setPdfLoading] = useState(false);

  const { data: deptsData } = useQuery({
    queryKey: ['departments'],
    queryFn: async () => {
      const { data } = await api.get('/departments');
      return data as { data: Department[] };
    },
  });
  const deptMap = new Map((deptsData?.data ?? []).map((d) => [d.id, d.name]));

  const { data: po, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['purchase-order', id],
    queryFn: async () => {
      const { data } = await api.get(`/purchase-orders/${id}`);
      return data.data as PurchaseOrder;
    },
    enabled: Boolean(id),
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['purchase-order', id] });
    queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
  };

  const submit = useMutation({
    mutationFn: () => api.post(`/purchase-orders/${id}/submit`),
    onSuccess: () => { refresh(); showToast({ title: t('page.po.toast_submitted'), variant: 'success' }); },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';
      showToast({ title: t('page.po.error_submit'), description: detail, variant: 'error' });
    },
  });

  const approve = useMutation({
    mutationFn: () => api.post(`/purchase-orders/${id}/approve`),
    onSuccess: () => { refresh(); showToast({ title: t('page.po.toast_approved'), variant: 'success' }); },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';
      showToast({ title: t('page.po.error_approve'), description: detail, variant: 'error' });
    },
  });

  const reject = useMutation({
    mutationFn: () => api.post(`/purchase-orders/${id}/reject`, { reason: rejectReason }),
    onSuccess: () => { refresh(); setShowReject(false); setRejectReason(''); showToast({ title: t('page.po.toast_rejected'), variant: 'success' }); },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';
      showToast({ title: t('page.po.error_reject'), description: detail, variant: 'error' });
    },
  });

  const markOrdered = useMutation({
    mutationFn: () => api.post(`/purchase-orders/${id}/mark-ordered`),
    onSuccess: () => { refresh(); showToast({ title: t('page.po.toast_ordered'), variant: 'success' }); },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';
      showToast({ title: t('page.po.error_order'), description: detail, variant: 'error' });
    },
  });

  const cancel = useMutation({
    mutationFn: () => api.post(`/purchase-orders/${id}/cancel`, { reason: cancelReason }),
    onSuccess: () => { refresh(); setShowCancel(false); setCancelReason(''); showToast({ title: t('page.po.toast_cancelled'), variant: 'success' }); },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';
      showToast({ title: t('page.po.error_cancel'), description: detail, variant: 'error' });
    },
  });

  const receiveItems = useMutation({
    mutationFn: (items: ReceiveInput[]) => api.post(`/purchase-orders/${id}/receive`, { items }),
    onSuccess: () => {
      refresh();
      setReceiveQtys({});
      setCreateAssets({});
      showToast({ title: t('page.po.toast_received'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';
      showToast({ title: t('page.po.error_receive'), description: detail, variant: 'error' });
    },
  });

  const closePo = useMutation({
    mutationFn: () => api.post(`/purchase-orders/${id}/close`),
    onSuccess: () => { refresh(); showToast({ title: t('page.po.toast_closed'), variant: 'success' }); },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';
      showToast({ title: t('page.po.error_close'), description: detail, variant: 'error' });
    },
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail} onRetry={() => { void refetch(); }} />;
  if (!po) return <ErrorState message={t('page.po.not_found')} />;

  const cancellable = ['DRAFT', 'SUBMITTED', 'APPROVED', 'ORDERED'].includes(po.status);
  const receivable = po.status === 'ORDERED' || po.status === 'PARTIALLY_RECEIVED';
  const closable = po.status === 'RECEIVED' || po.status === 'PARTIALLY_RECEIVED';
  const currentStep = STATUS_FLOW.indexOf(po.status);
  const pdfEligible = ['APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED', 'RECEIVED', 'CLOSED'].includes(po.status);

  const handleDownloadPdf = async () => {
    setPdfLoading(true);
    try {
      await api.post(`/purchase-orders/${po.id}/pdf`);
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const { data } = await api.get(`/purchase-orders/${po.id}/pdf`);
      window.open(data.data.download_url, '_blank');
    } catch {
      showToast({ title: t('page.po.error_pdf'), variant: 'error' });
    } finally {
      setPdfLoading(false);
    }
  };

  const handleReceive = () => {
    const items: ReceiveInput[] = [];
    for (const item of po.items) {
      const qty = receiveQtys[item.id] || 0;
      if (qty > 0) {
        items.push({
          item_id: item.id,
          received_quantity: qty,
          create_asset: createAssets[item.id] || false,
        });
      }
    }
    if (items.length === 0) return;
    receiveItems.mutate(items);
  };

  const hasReceiveInput = Object.values(receiveQtys).some((q) => q > 0);

  const progressPct = (item: PurchaseOrderItem) =>
    item.quantity > 0 ? Math.round((item.received_quantity / item.quantity) * 100) : 0;

  const progressColor = (pct: number) =>
    pct >= 100 ? 'bg-success' : pct > 0 ? 'bg-warning' : 'bg-muted';

  // Timeline steps derived from status flow
  const timelineSteps = po.status === 'CANCELLED'
    ? [
        { label: t('page.po.status_draft'), status: 'completed' as const, date: po.created_at },
        { label: t('page.po.status_cancelled'), status: 'rejected' as const, date: undefined },
      ]
    : STATUS_FLOW.map((step, i) => ({
        label: t(`page.po.status_${step.toLowerCase()}`),
        status: (i < currentStep ? 'completed' : i === currentStep ? 'current' : 'pending') as 'completed' | 'current' | 'pending',
        date: step === 'DRAFT' && po.created_at ? po.created_at
          : step === 'APPROVED' && po.approved_at ? po.approved_at
          : step === 'ORDERED' && po.ordered_at ? po.ordered_at
          : undefined,
      }));

  const completedSteps = timelineSteps.filter(s => s.status === 'completed').length;
  const totalSteps = timelineSteps.length;
  const progressWidth = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

  const STEP_STYLES = {
    completed: { iconBg: 'bg-success/15', iconColor: 'text-success', lineColor: 'bg-success/40', labelColor: 'text-foreground' },
    current: { iconBg: 'bg-primary/15', iconColor: 'text-primary', lineColor: 'bg-border', labelColor: 'text-primary' },
    pending: { iconBg: 'bg-muted', iconColor: 'text-muted-foreground', lineColor: 'bg-border', labelColor: 'text-muted-foreground' },
    rejected: { iconBg: 'bg-destructive/10', iconColor: 'text-destructive', lineColor: 'bg-destructive/30', labelColor: 'text-destructive' },
  };

  const showReceiptCol = receivable || po.status === 'RECEIVED' || po.status === 'CLOSED' || po.status === 'PARTIALLY_RECEIVED';

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Link
            to="/purchase-orders"
            className="inline-flex items-center justify-center gap-1.5 rounded-md h-8 px-3 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
          >
            <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="m15 18-6-6 6-6" />
            </svg>
            {t('page.po.back')}
          </Link>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-semibold text-foreground">{po.po_number}</h1>
            <Badge variant={STATUS_VARIANT[po.status] || 'default'}>
              {t(`page.po.status_${po.status.toLowerCase()}`)}
            </Badge>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {po.status === 'DRAFT' && (
            <>
              <Link
                to={`/purchase-orders/${po.id}/edit`}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
              >
                {t('common.edit')}
              </Link>
              <button
                onClick={() => submit.mutate()}
                disabled={submit.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {submit.isPending ? t('common.working') : t('page.po.action_submit')}
              </button>
            </>
          )}
          {po.status === 'SUBMITTED' && isAdmin && (
            <>
              <button
                onClick={() => setShowReject(true)}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border border-destructive/30 text-destructive bg-background shadow-xs hover:bg-destructive/10 transition-all"
              >
                {t('page.po.action_reject')}
              </button>
              <button
                onClick={() => approve.mutate()}
                disabled={approve.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {approve.isPending ? t('common.working') : t('page.po.action_approve')}
              </button>
            </>
          )}
          {po.status === 'APPROVED' && (
            <button
              onClick={() => markOrdered.mutate()}
              disabled={markOrdered.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {markOrdered.isPending ? t('common.working') : t('page.po.action_mark_ordered')}
            </button>
          )}
          {closable && (
            <button
              onClick={() => closePo.mutate()}
              disabled={closePo.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-success text-white shadow-xs transition-all hover:bg-success/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {closePo.isPending ? t('common.working') : t('page.po.action_close')}
            </button>
          )}
          {pdfEligible && (
            <button
              onClick={handleDownloadPdf}
              disabled={pdfLoading}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
            >
              {pdfLoading ? t('common.working') : t('page.po.download_pdf')}
            </button>
          )}
          {cancellable && (
            <button
              onClick={() => setShowCancel(true)}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border border-destructive/30 text-destructive bg-background shadow-xs hover:bg-destructive/10 transition-all"
            >
              {t('page.po.action_cancel')}
            </button>
          )}
        </div>
      </div>

      {/* Reject / Cancel forms */}
      {(showReject || showCancel) && (
        <div className="rounded-lg border border-border bg-card p-5">
          {showReject && (
            <div className="space-y-3">
              <label className="block mb-1.5 text-muted-foreground">{t('page.po.reject_reason')}</label>
              <textarea value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} rows={2} className="w-full bg-card" />
              <div className="flex justify-end gap-2">
                <button onClick={() => setShowReject(false)} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all">{t('common.cancel')}</button>
                <button onClick={() => reject.mutate()} disabled={reject.isPending || !rejectReason.trim()} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50">
                  {reject.isPending ? t('common.working') : t('page.po.action_reject')}
                </button>
              </div>
            </div>
          )}
          {showCancel && (
            <div className="space-y-3">
              <label className="block mb-1.5 text-muted-foreground">{t('page.po.cancel_reason')}</label>
              <textarea value={cancelReason} onChange={(e) => setCancelReason(e.target.value)} rows={2} className="w-full bg-card" />
              <div className="flex justify-end gap-2">
                <button onClick={() => setShowCancel(false)} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all">{t('common.cancel')}</button>
                <button onClick={() => cancel.mutate()} disabled={cancel.isPending || !cancelReason.trim()} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50">
                  {cancel.isPending ? t('common.working') : t('page.po.action_cancel')}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Cancellation banner */}
      {po.cancellation_reason && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-5 py-4">
          <span className="text-sm font-medium text-destructive">{t('page.po.cancellation_reason')}:</span>{' '}
          <span className="text-sm text-destructive">{po.cancellation_reason}</span>
        </div>
      )}

      {/* Two-column grid — v0 layout */}
      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        {/* Left Column */}
        <div className="flex flex-col gap-6">
          {/* Order Information Card */}
          <div className="rounded-lg border border-border bg-card">
            <div className="border-b border-border px-5 py-3.5">
              <h3 className="text-sm font-medium text-foreground">{t('page.po.order_info')}</h3>
            </div>
            <div className="grid gap-4 p-5 sm:grid-cols-2">
              {/* Vendor */}
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <svg className="h-4 w-4 text-primary" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M3 9h18v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9Z" />
                    <path d="m3 9 2.45-4.9A2 2 0 0 1 7.24 3h9.52a2 2 0 0 1 1.8 1.1L21 9" />
                    <path d="M12 3v6" />
                  </svg>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-muted-foreground">{t('page.po.vendor')}</span>
                  <span className="text-sm font-medium text-foreground">{po.vendor_name}</span>
                </div>
              </div>
              {/* Department */}
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <svg className="h-4 w-4 text-primary" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <rect width="16" height="20" x="4" y="2" rx="2" ry="2" />
                    <path d="M9 22v-4h6v4" />
                    <path d="M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01" />
                  </svg>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-muted-foreground">{t('page.po.department')}</span>
                  <span className="text-sm font-medium text-foreground">{deptMap.get(po.department_id) || po.department_id}</span>
                </div>
              </div>
              {/* Date */}
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <svg className="h-4 w-4 text-primary" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <rect width="18" height="18" x="3" y="4" rx="2" ry="2" />
                    <path d="M16 2v4M8 2v4M3 10h18" />
                  </svg>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-muted-foreground">{t('page.po.date')}</span>
                  <span className="text-sm font-medium text-foreground">{po.created_at ? formatDate(po.created_at) : '—'}</span>
                </div>
              </div>
              {/* Items count */}
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <svg className="h-4 w-4 text-primary" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M4 9V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v4" />
                    <path d="M8 8v1M12 8v1M16 8v1" />
                    <rect width="20" height="12" x="2" y="9" rx="2" />
                  </svg>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-muted-foreground">{t('page.po.items')}</span>
                  <span className="text-sm font-medium text-foreground">
                    {po.items.reduce((acc, i) => acc + i.quantity, 0)} item(s)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Items Table */}
          <div className="rounded-lg border border-border bg-card overflow-hidden">
            <div className="border-b border-border px-5 py-3.5">
              <h3 className="text-sm font-medium text-foreground">{t('page.po.items_detail')}</h3>
            </div>
            <Table>
              <thead>
                <tr className="hover:bg-transparent">
                  <Th className="pl-5">{t('page.po.item_desc')}</Th>
                  <Th>{t('page.po.item_type')}</Th>
                  <Th className="text-right">{t('page.po.item_unit_cost')}</Th>
                  <Th className="text-right">{t('page.po.item_qty')}</Th>
                  <Th className="text-right pr-5">{t('page.po.item_total')}</Th>
                  {showReceiptCol && <Th>{t('page.po.receipt_progress')}</Th>}
                </tr>
              </thead>
              <tbody>
                {po.items.map((item) => {
                  const pct = progressPct(item);
                  return (
                    <Tr key={item.id}>
                      <Td className="pl-5">
                        <span className="text-sm font-medium text-foreground">{item.description}</span>
                        {item.linked_asset_id && (
                          <Link to={`/assets/${item.linked_asset_id}`} className="ml-2 text-xs text-primary hover:underline">
                            {t('page.po.view_asset')}
                          </Link>
                        )}
                      </Td>
                      <Td>
                        <span className="text-sm text-muted-foreground">
                          {item.asset_type ? t(`enum.${item.asset_type}`, undefined, { defaultValue: item.asset_type }) : '—'}
                        </span>
                      </Td>
                      <Td className="text-right">
                        <span className="text-sm text-muted-foreground">{formatCents(item.unit_cost_cents, po.currency)}</span>
                      </Td>
                      <Td className="text-right">
                        <span className="text-sm text-foreground">{item.quantity}</span>
                      </Td>
                      <Td className="text-right pr-5">
                        <span className="text-sm font-medium text-foreground">{formatCents(item.total_cost_cents, po.currency)}</span>
                      </Td>
                      {showReceiptCol && (
                        <Td>
                          <div className="flex items-center gap-2">
                            <div className="w-20 h-1.5 rounded-full bg-muted overflow-hidden">
                              <div className={`h-full rounded-full ${progressColor(pct)}`} style={{ width: `${Math.min(pct, 100)}%` }} />
                            </div>
                            <span className="text-xs text-muted-foreground">{item.received_quantity}/{item.quantity}</span>
                            {item.received_quantity >= item.quantity && <Badge variant="success">{t('page.po.fully_received')}</Badge>}
                          </div>
                        </Td>
                      )}
                    </Tr>
                  );
                })}
              </tbody>
            </Table>
            <div className="flex items-center justify-end border-t border-border px-5 py-3.5">
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">{t('page.po.total')}:</span>
                <span className="text-lg font-semibold text-foreground">{formatCents(po.total_amount_cents, po.currency)}</span>
              </div>
            </div>
          </div>

          {/* Receipt form */}
          {receivable && (
            <div className="rounded-lg border border-border bg-card overflow-hidden">
              <div className="border-b border-border px-5 py-3.5">
                <h3 className="text-sm font-medium text-foreground">{t('page.po.receive_items')}</h3>
              </div>
              <Table>
                <thead>
                  <tr className="hover:bg-transparent">
                    <Th className="pl-5">{t('page.po.item_desc')}</Th>
                    <Th>{t('page.po.ordered')}</Th>
                    <Th>{t('page.po.already_received')}</Th>
                    <Th>{t('page.po.remaining')}</Th>
                    <Th>{t('page.po.receive_qty')}</Th>
                    <Th>{t('page.po.create_asset')}</Th>
                  </tr>
                </thead>
                <tbody>
                  {po.items.map((item) => {
                    const remaining = item.quantity - item.received_quantity;
                    return (
                      <Tr key={item.id}>
                        <Td className="pl-5">{item.description}</Td>
                        <Td>{item.quantity}</Td>
                        <Td>{item.received_quantity}</Td>
                        <Td>{remaining}</Td>
                        <Td>
                          {remaining > 0 ? (
                            <input
                              type="number"
                              min={0}
                              max={remaining}
                              value={receiveQtys[item.id] || ''}
                              onChange={(e) => setReceiveQtys((prev) => ({
                                ...prev,
                                [item.id]: Math.min(parseInt(e.target.value) || 0, remaining),
                              }))}
                              className="w-20 text-sm"
                            />
                          ) : (
                            <span className="text-xs text-success">{t('page.po.fully_received')}</span>
                          )}
                        </Td>
                        <Td>
                          {remaining > 0 && item.asset_type && !item.linked_asset_id && (
                            <input
                              type="checkbox"
                              checked={createAssets[item.id] || false}
                              onChange={(e) => setCreateAssets((prev) => ({
                                ...prev,
                                [item.id]: e.target.checked,
                              }))}
                              className="h-4 w-4 rounded border-input"
                            />
                          )}
                        </Td>
                      </Tr>
                    );
                  })}
                </tbody>
              </Table>
              <div className="border-t border-border px-5 py-3.5">
                <button
                  onClick={handleReceive}
                  disabled={receiveItems.isPending || !hasReceiveInput}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {receiveItems.isPending ? t('common.working') : t('page.po.action_receive')}
                </button>
              </div>
            </div>
          )}

          {/* Notes */}
          {po.notes && (
            <div className="rounded-lg border border-border bg-card">
              <div className="border-b border-border px-5 py-3.5">
                <div className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
                    <path d="M14 2v4a2 2 0 0 0 2 2h4" />
                  </svg>
                  <h3 className="text-sm font-medium text-foreground">{t('page.po.notes')}</h3>
                </div>
              </div>
              <div className="px-5 py-4">
                <p className="text-sm text-foreground leading-relaxed">{po.notes}</p>
              </div>
            </div>
          )}

          {/* Linked requests */}
          {po.request_ids.length > 0 && (
            <div className="rounded-lg border border-border bg-card">
              <div className="border-b border-border px-5 py-3.5">
                <h3 className="text-sm font-medium text-foreground">{t('page.po.linked_requests')}</h3>
              </div>
              <div className="flex flex-wrap gap-2 px-5 py-4">
                {po.request_ids.map((rid) => (
                  <Link key={rid} to={`/requests/${rid}`} className="text-sm text-primary hover:underline">
                    {rid.slice(0, 8)}...
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column — Status Timeline (v0 approval-timeline style) */}
        <div className="flex flex-col gap-6">
          <div className="rounded-lg border border-border bg-card">
            <div className="border-b border-border px-5 py-3.5">
              <h3 className="text-sm font-medium text-foreground">{t('page.po.timeline')}</h3>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {t('page.po.steps_completed', { done: String(completedSteps), total: String(totalSteps) })}
              </p>
            </div>
            {/* Progress bar */}
            <div className="px-5 pt-4">
              <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-500"
                  style={{ width: `${progressWidth}%` }}
                />
              </div>
            </div>
            <div className="mt-4 border-t border-border" />
            {/* Vertical timeline */}
            <div className="p-5">
              <div className="flex flex-col">
                {timelineSteps.map((step, index) => {
                  const isLast = index === timelineSteps.length - 1;
                  const style = STEP_STYLES[step.status];
                  return (
                    <div key={index} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-colors ${style.iconBg} ${step.status === 'current' ? 'ring-4 ring-primary/10' : ''}`}>
                          {step.status === 'completed' ? (
                            <svg className={`h-4 w-4 ${style.iconColor}`} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="m20 6-11 11-5-5" /></svg>
                          ) : step.status === 'current' ? (
                            <svg className={`h-4 w-4 ${style.iconColor}`} fill="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" /></svg>
                          ) : step.status === 'rejected' ? (
                            <svg className={`h-4 w-4 ${style.iconColor}`} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="m18 6-12 12M6 6l12 12" /></svg>
                          ) : (
                            <svg className={`h-4 w-4 ${style.iconColor}`} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>
                          )}
                        </div>
                        {!isLast && (
                          <div className={`w-0.5 flex-1 min-h-8 ${style.lineColor}`} />
                        )}
                      </div>
                      <div className={`flex-1 ${isLast ? 'pb-0' : 'pb-6'}`}>
                        <div className="flex flex-col gap-0.5 -mt-0.5">
                          <span className={`text-sm font-medium ${style.labelColor}`}>
                            {step.label}
                          </span>
                          {step.date && (
                            <span className="text-xs text-muted-foreground mt-0.5">
                              {formatDateTime(step.date)}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
