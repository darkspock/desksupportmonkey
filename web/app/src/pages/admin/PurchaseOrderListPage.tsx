import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { Tooltip } from '../../components/ui/Tooltip';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';
import { useAuth } from '../../contexts/AuthContext';
import type { PurchaseOrder, PaginatedResponse, Vendor, Department } from '../../types';

const STATUS_OPTIONS = ['', 'DRAFT', 'SUBMITTED', 'APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED', 'RECEIVED', 'CLOSED', 'CANCELLED'];

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

function RowActionIcon({ kind }: { kind: string }) {
  switch (kind) {
    case 'submit':
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="m22 2-7 20-4-9-9-4Z" />
          <path d="M22 2 11 13" />
        </svg>
      );
    case 'approve':
    case 'close':
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="m20 6-11 11-5-5" />
        </svg>
      );
    case 'mark-ordered':
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M3 7h15l3 5-3 5H3z" />
        </svg>
      );
    case 'receive':
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M21 8a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v8h18z" />
          <path d="M7 12h.01M12 12h.01M17 12h.01" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      );
  }
}

interface RowAction {
  key: string;
  label: string;
  title: string;
  to?: string;
  onClick?: () => void;
  tone?: 'default' | 'danger' | 'success';
  disabled?: boolean;
}

type PendingAction = { poId: string; key: 'submit' | 'approve' | 'mark-ordered' | 'close' };

export default function PurchaseOrderListPage() {
  const { t } = useI18n();
  const { showToast } = useToast();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin' || user?.role === 'procurement_manager';

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [vendorFilter, setVendorFilter] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const pageSize = 20;

  const refreshPOs = () => {
    queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
    queryClient.invalidateQueries({ queryKey: ['purchase-order'] });
    queryClient.invalidateQueries({ queryKey: ['po-stats'] });
  };

  const errorDetail = (err: unknown) =>
    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';

  const submitPo = useMutation({
    mutationFn: async (poId: string) => api.post(`/purchase-orders/${poId}/submit`),
    onSuccess: () => {
      refreshPOs();
      showToast({ title: t('page.po.toast_submitted'), variant: 'success' });
    },
    onError: (err: unknown) => {
      showToast({ title: t('page.po.error_submit'), description: errorDetail(err), variant: 'error' });
    },
  });

  const approvePo = useMutation({
    mutationFn: async (poId: string) => api.post(`/purchase-orders/${poId}/approve`),
    onSuccess: () => {
      refreshPOs();
      showToast({ title: t('page.po.toast_approved'), variant: 'success' });
    },
    onError: (err: unknown) => {
      showToast({ title: t('page.po.error_approve'), description: errorDetail(err), variant: 'error' });
    },
  });

  const markOrderedPo = useMutation({
    mutationFn: async (poId: string) => api.post(`/purchase-orders/${poId}/mark-ordered`),
    onSuccess: () => {
      refreshPOs();
      showToast({ title: t('page.po.toast_ordered'), variant: 'success' });
    },
    onError: (err: unknown) => {
      showToast({ title: t('page.po.error_order'), description: errorDetail(err), variant: 'error' });
    },
  });

  const closePo = useMutation({
    mutationFn: async (poId: string) => api.post(`/purchase-orders/${poId}/close`),
    onSuccess: () => {
      refreshPOs();
      showToast({ title: t('page.po.toast_closed'), variant: 'success' });
    },
    onError: (err: unknown) => {
      showToast({ title: t('page.po.error_close'), description: errorDetail(err), variant: 'error' });
    },
  });

  const iconButtonClass = (tone: 'default' | 'danger' | 'success' = 'default') =>
    tone === 'danger'
      ? 'inline-flex h-8 w-8 items-center justify-center rounded-md border border-destructive/20 bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors disabled:opacity-50'
      : tone === 'success'
      ? 'inline-flex h-8 w-8 items-center justify-center rounded-md border border-success/20 bg-success/10 text-success hover:bg-success/20 transition-colors disabled:opacity-50'
      : 'inline-flex h-8 w-8 items-center justify-center rounded-md border border-primary/20 bg-primary/10 text-primary hover:bg-primary/20 transition-colors disabled:opacity-50';

  const { data: vendorsData } = useQuery({
    queryKey: ['vendors-active'],
    queryFn: async () => {
      const { data } = await api.get('/vendors?page_size=100&is_active=true');
      return data as PaginatedResponse<Vendor>;
    },
  });

  const { data: deptsData } = useQuery({
    queryKey: ['departments'],
    queryFn: async () => {
      const { data } = await api.get('/departments');
      return data as PaginatedResponse<Department>;
    },
  });

  const vendors = vendorsData?.data ?? [];
  const departments = deptsData?.data ?? [];
  const deptMap = new Map(departments.map((d) => [d.id, d.name]));

  // Stats query — fetches all POs to compute status counts
  const { data: statsData } = useQuery({
    queryKey: ['po-stats'],
    queryFn: async () => {
      const { data } = await api.get('/purchase-orders?page_size=100');
      return data as PaginatedResponse<PurchaseOrder>;
    },
    staleTime: 30_000,
  });

  const statsCounts = useMemo(() => {
    const all = statsData?.data ?? [];
    return {
      total: statsData?.meta?.total ?? 0,
      pending: all.filter(p => p.status === 'DRAFT' || p.status === 'SUBMITTED').length,
      approved: all.filter(p => p.status === 'APPROVED' || p.status === 'ORDERED').length,
      cancelled: all.filter(p => p.status === 'CANCELLED').length,
      completed: all.filter(p => p.status === 'RECEIVED' || p.status === 'PARTIALLY_RECEIVED' || p.status === 'CLOSED').length,
    };
  }, [statsData]);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['purchase-orders', page, statusFilter, vendorFilter, deptFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', String(pageSize));
      if (statusFilter) params.set('status', statusFilter);
      if (vendorFilter) params.set('vendor_id', vendorFilter);
      if (deptFilter) params.set('department_id', deptFilter);
      const { data } = await api.get(`/purchase-orders?${params}`);
      return data as PaginatedResponse<PurchaseOrder>;
    },
  });

  const pos = data?.data ?? [];
  const total = data?.meta?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  // Client-side search filtering on current page
  const filteredPos = useMemo(() => {
    if (!search.trim()) return pos;
    const s = search.toLowerCase();
    return pos.filter(po =>
      po.po_number.toLowerCase().includes(s) ||
      po.vendor_name.toLowerCase().includes(s) ||
      (deptMap.get(po.department_id) || '').toLowerCase().includes(s)
    );
  }, [pos, search, deptMap]);

  const mutationBusy = submitPo.isPending || approvePo.isPending || markOrderedPo.isPending || closePo.isPending;

  const primaryActionFor = (po: PurchaseOrder): RowAction => {
    switch (po.status) {
      case 'DRAFT':
        return {
          key: 'submit',
          label: t('page.po.action_submit'),
          title: t('page.po.action_submit'),
          onClick: () => setPendingAction({ poId: po.id, key: 'submit' }),
          disabled: mutationBusy,
        };
      case 'SUBMITTED':
        if (isAdmin) {
          return {
            key: 'approve',
            label: t('page.po.action_approve'),
            title: t('page.po.action_approve'),
            onClick: () => setPendingAction({ poId: po.id, key: 'approve' }),
            disabled: mutationBusy,
            tone: 'success',
          };
        }
        return {
          key: 'details',
          label: t('table.details'),
          title: t('table.details'),
          to: `/purchase-orders/${po.id}`,
        };
      case 'APPROVED':
        return {
          key: 'mark-ordered',
          label: t('page.po.action_mark_ordered'),
          title: t('page.po.action_mark_ordered'),
          onClick: () => setPendingAction({ poId: po.id, key: 'mark-ordered' }),
          disabled: mutationBusy,
        };
      case 'ORDERED':
      case 'PARTIALLY_RECEIVED':
        return {
          key: 'receive',
          label: t('page.po.action_receive'),
          title: t('page.po.action_receive'),
          to: `/purchase-orders/${po.id}`,
        };
      case 'RECEIVED':
        return {
          key: 'close',
          label: t('page.po.action_close'),
          title: t('page.po.action_close'),
          onClick: () => setPendingAction({ poId: po.id, key: 'close' }),
          disabled: mutationBusy,
          tone: 'success',
        };
      case 'CLOSED':
      case 'CANCELLED':
      default:
        return {
          key: 'details',
          label: t('table.details'),
          title: t('table.details'),
          to: `/purchase-orders/${po.id}`,
        };
    }
  };

  const secondaryActionsFor = (po: PurchaseOrder, primaryKey: string): RowAction[] => {
    const cancellable = ['DRAFT', 'SUBMITTED', 'APPROVED', 'ORDERED'].includes(po.status);
    const actions: RowAction[] = [
      {
        key: 'details',
        label: t('table.details'),
        title: t('table.details'),
        to: `/purchase-orders/${po.id}`,
      },
    ];

    if (po.status === 'DRAFT') {
      actions.push({
        key: 'edit',
        label: t('common.edit'),
        title: t('common.edit'),
        to: `/purchase-orders/${po.id}/edit`,
      });
      actions.push({
        key: 'submit',
        label: t('page.po.action_submit'),
        title: t('page.po.action_submit'),
        onClick: () => setPendingAction({ poId: po.id, key: 'submit' }),
        disabled: mutationBusy,
      });
    }

    if (po.status === 'SUBMITTED' && isAdmin) {
      actions.push({
        key: 'approve',
        label: t('page.po.action_approve'),
        title: t('page.po.action_approve'),
        onClick: () => setPendingAction({ poId: po.id, key: 'approve' }),
        disabled: mutationBusy,
        tone: 'success',
      });
      actions.push({
        key: 'reject',
        label: t('page.po.action_reject'),
        title: t('page.po.action_reject'),
        to: `/purchase-orders/${po.id}`,
      });
    }

    if (po.status === 'APPROVED') {
      actions.push({
        key: 'mark-ordered',
        label: t('page.po.action_mark_ordered'),
        title: t('page.po.action_mark_ordered'),
        onClick: () => setPendingAction({ poId: po.id, key: 'mark-ordered' }),
        disabled: mutationBusy,
      });
    }

    if (po.status === 'ORDERED' || po.status === 'PARTIALLY_RECEIVED') {
      actions.push({
        key: 'receive',
        label: t('page.po.action_receive'),
        title: t('page.po.action_receive'),
        to: `/purchase-orders/${po.id}`,
      });
    }

    if (po.status === 'PARTIALLY_RECEIVED' || po.status === 'RECEIVED') {
      actions.push({
        key: 'close',
        label: t('page.po.action_close'),
        title: t('page.po.action_close'),
        onClick: () => setPendingAction({ poId: po.id, key: 'close' }),
        disabled: mutationBusy,
        tone: 'success',
      });
    }

    if (cancellable) {
      actions.push({
        key: 'cancel',
        label: t('page.po.action_cancel'),
        title: t('page.po.action_cancel'),
        to: `/purchase-orders/${po.id}`,
        tone: 'danger',
      });
    }

    return actions.filter((action) => action.key !== primaryKey);
  };

  const confirmTitle = pendingAction
    ? pendingAction.key === 'submit'
      ? t('page.po.confirm_submit_title')
      : pendingAction.key === 'approve'
      ? t('page.po.confirm_approve_title')
      : pendingAction.key === 'mark-ordered'
      ? t('page.po.confirm_mark_ordered_title')
      : t('page.po.confirm_close_title')
    : '';

  const confirmDescription = pendingAction
    ? pendingAction.key === 'submit'
      ? t('page.po.confirm_submit_desc')
      : pendingAction.key === 'approve'
      ? t('page.po.confirm_approve_desc')
      : pendingAction.key === 'mark-ordered'
      ? t('page.po.confirm_mark_ordered_desc')
      : t('page.po.confirm_close_desc')
    : '';

  const confirmLabel = pendingAction
    ? pendingAction.key === 'submit'
      ? t('page.po.action_submit')
      : pendingAction.key === 'approve'
      ? t('page.po.action_approve')
      : pendingAction.key === 'mark-ordered'
      ? t('page.po.action_mark_ordered')
      : t('page.po.action_close')
    : '';

  const runPendingAction = () => {
    if (!pendingAction) return;
    if (pendingAction.key === 'submit') submitPo.mutate(pendingAction.poId);
    if (pendingAction.key === 'approve') approvePo.mutate(pendingAction.poId);
    if (pendingAction.key === 'mark-ordered') markOrderedPo.mutate(pendingAction.poId);
    if (pendingAction.key === 'close') closePo.mutate(pendingAction.poId);
    setPendingAction(null);
  };

  const statItems = [
    {
      label: t('page.po.stat_total'),
      value: statsCounts.total,
      colorClass: 'text-primary',
      bgClass: 'bg-primary/10',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
          <path d="M15 2H9a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1Z" />
          <path d="M12 11h4M12 16h4M8 11h.01M8 16h.01" />
        </svg>
      ),
    },
    {
      label: t('page.po.stat_pending'),
      value: statsCounts.pending,
      colorClass: 'text-warning-foreground',
      bgClass: 'bg-warning/15',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 6v6l4 2" />
        </svg>
      ),
    },
    {
      label: t('page.po.stat_approved'),
      value: statsCounts.approved,
      colorClass: 'text-success',
      bgClass: 'bg-success/15',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <path d="m9 11 3 3L22 4" />
        </svg>
      ),
    },
    {
      label: t('page.po.stat_cancelled'),
      value: statsCounts.cancelled,
      colorClass: 'text-destructive',
      bgClass: 'bg-destructive/10',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="m15 9-6 6M9 9l6 6" />
        </svg>
      ),
    },
    {
      label: t('page.po.stat_completed'),
      value: statsCounts.completed,
      colorClass: 'text-muted-foreground',
      bgClass: 'bg-muted',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2" />
          <path d="M15 18H9" />
          <path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14" />
          <circle cx="17" cy="18" r="2" />
          <circle cx="7" cy="18" r="2" />
        </svg>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {t('page.po.title')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('page.po.subtitle')}
          </p>
        </div>
        <Link
          to="/purchase-orders/new"
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M5 12h14M12 5v14" />
          </svg>
          {t('page.po.new_po')}
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {statItems.map((stat) => (
          <div
            key={stat.label}
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-3.5"
          >
            <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${stat.bgClass}`}>
              <span className={stat.colorClass}>{stat.icon}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-semibold leading-none text-foreground">{stat.value}</span>
              <span className="mt-1 text-xs text-muted-foreground">{stat.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <svg
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            type="search"
            placeholder={t('page.po.search_placeholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 bg-card"
          />
        </div>
        <div className="flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="w-[160px] bg-card"
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s ? t(`page.po.status_${s.toLowerCase()}`) : t('page.po.filter_all_statuses')}
              </option>
            ))}
          </select>
          <select
            value={vendorFilter}
            onChange={(e) => { setVendorFilter(e.target.value); setPage(1); }}
            className="w-[160px] bg-card"
          >
            <option value="">{t('page.po.filter_all_vendors')}</option>
            {vendors.map((v) => (
              <option key={v.id} value={v.id}>{v.name}</option>
            ))}
          </select>
          <select
            value={deptFilter}
            onChange={(e) => { setDeptFilter(e.target.value); setPage(1); }}
            className="hidden lg:block w-[160px] bg-card"
          >
            <option value="">{t('page.po.filter_all_depts')}</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? <Loading /> : isError ? (
        <ErrorState
          message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.po.error_load')}
          onRetry={() => { void refetch(); }}
        />
      ) : !filteredPos.length ? (
        <EmptyState message={t('page.po.empty')} />
      ) : (
        <>
          <Table>
            <thead>
              <tr className="hover:bg-transparent">
                <Th className="pl-4">{t('page.po.po_number')}</Th>
                <Th>{t('page.po.vendor')}</Th>
                <Th className="hidden md:table-cell">{t('page.po.department')}</Th>
                <Th className="hidden sm:table-cell">{t('page.po.date')}</Th>
                <Th>{t('table.status')}</Th>
                <Th className="text-right">{t('page.po.total')}</Th>
                <Th className="w-12 pr-4">
                  <span className="sr-only">{t('table.actions')}</span>
                </Th>
              </tr>
            </thead>
            <tbody>
              {filteredPos.map((po) => {
                const primaryAction = primaryActionFor(po);
                const secondaryActions = secondaryActionsFor(po, primaryAction.key);
                return (
                  <Tr key={po.id}>
                    <Td className="pl-4">
                      <Link
                        to={`/purchase-orders/${po.id}`}
                        className="font-mono text-sm font-medium text-foreground hover:text-primary transition-colors"
                      >
                        {po.po_number}
                      </Link>
                    </Td>
                    <Td>
                      <span className="text-sm font-medium text-foreground">{po.vendor_name}</span>
                    </Td>
                    <Td className="hidden md:table-cell">
                      <span className="text-sm text-muted-foreground">{deptMap.get(po.department_id) || po.department_id}</span>
                    </Td>
                    <Td className="hidden sm:table-cell">
                      <span className="text-sm text-muted-foreground">{po.created_at ? formatDate(po.created_at) : '—'}</span>
                    </Td>
                    <Td>
                      <Badge variant={STATUS_VARIANT[po.status] || 'default'}>
                        {t(`page.po.status_${po.status.toLowerCase()}`)}
                      </Badge>
                    </Td>
                    <Td className="text-right">
                      <span className="text-sm font-medium text-foreground">{formatCents(po.total_amount_cents, po.currency)}</span>
                    </Td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center justify-end gap-2">
                        <Tooltip content={primaryAction.title}>
                          {primaryAction.to ? (
                            <Link
                              to={primaryAction.to}
                              aria-label={primaryAction.title}
                              className={iconButtonClass(primaryAction.tone)}
                            >
                              <RowActionIcon kind={primaryAction.key} />
                            </Link>
                          ) : (
                            <button
                              type="button"
                              onClick={() => { primaryAction.onClick?.(); setOpenMenuId(null); }}
                              disabled={primaryAction.disabled}
                              aria-label={primaryAction.title}
                              className={iconButtonClass(primaryAction.tone)}
                            >
                              <RowActionIcon kind={primaryAction.key} />
                            </button>
                          )}
                        </Tooltip>

                        <div className="relative">
                          <Tooltip content={t('page.po.more_actions')}>
                            <button
                              type="button"
                              className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                              aria-label={t('page.po.more_actions')}
                              onClick={() => setOpenMenuId((cur) => (cur === po.id ? null : po.id))}
                            >
                              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor" aria-hidden="true">
                                <circle cx="12" cy="5" r="2" />
                                <circle cx="12" cy="12" r="2" />
                                <circle cx="12" cy="19" r="2" />
                              </svg>
                            </button>
                          </Tooltip>
                          {openMenuId === po.id && (
                            <div className="absolute right-0 z-20 mt-2 min-w-[180px] rounded-lg border border-border bg-card p-1 shadow-lg">
                              <button
                                type="button"
                                className="block w-full rounded-md px-3 py-2 text-left text-xs text-muted-foreground hover:bg-accent"
                                onClick={() => setOpenMenuId(null)}
                              >
                                {t('common.close')}
                              </button>
                              {secondaryActions.map((action) => (
                                action.to ? (
                                  <Link
                                    key={action.key}
                                    to={action.to}
                                    className={`block rounded-md px-3 py-2 text-left text-xs hover:bg-accent ${action.tone === 'danger' ? 'text-destructive' : action.tone === 'success' ? 'text-success' : 'text-foreground'}`}
                                    title={action.title}
                                    onClick={() => setOpenMenuId(null)}
                                  >
                                    {action.label}
                                  </Link>
                                ) : (
                                  <button
                                    key={action.key}
                                    type="button"
                                    onClick={() => { action.onClick?.(); setOpenMenuId(null); }}
                                    disabled={action.disabled}
                                    className={`block w-full rounded-md px-3 py-2 text-left text-xs hover:bg-accent disabled:opacity-50 ${action.tone === 'danger' ? 'text-destructive' : action.tone === 'success' ? 'text-success' : 'text-foreground'}`}
                                    title={action.title}
                                  >
                                    {action.label}
                                  </button>
                                )
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                  </Tr>
                );
              })}
            </tbody>
          </Table>
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <span className="text-sm text-muted-foreground">{t('common.total', { count: String(total) })}</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="inline-flex items-center justify-center rounded-md h-8 px-3 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:pointer-events-none disabled:opacity-40"
                >
                  {t('common.prev')}
                </button>
                <span className="inline-flex items-center justify-center h-8 px-3 text-sm text-muted-foreground">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="inline-flex items-center justify-center rounded-md h-8 px-3 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:pointer-events-none disabled:opacity-40"
                >
                  {t('common.next')}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      <ConfirmDialog
        open={Boolean(pendingAction)}
        title={confirmTitle}
        description={confirmDescription}
        confirmLabel={confirmLabel}
        busy={mutationBusy}
        onConfirm={runPendingAction}
        onCancel={() => setPendingAction(null)}
      />
    </div>
  );
}
