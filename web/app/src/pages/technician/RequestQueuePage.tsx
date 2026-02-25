import { useState, useMemo, type DragEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CircleAlert,
  CircleCheck,
  CircleX,
  ClipboardList,
  Clock3,
  EllipsisVertical,
  Eye,
  Kanban,
  List,
  LoaderCircle,
  Search,
} from 'lucide-react';
import api from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Pagination } from '../../components/ui/Pagination';
import { Tooltip } from '../../components/ui/Tooltip';
import { CustomFieldFilters } from '../../components/custom-fields/CustomFieldFilters';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';
import { WorkflowIcon } from '../../components/ui/WorkflowIcon';
import type { ServiceRequest, PaginatedResponse, AssignableUser, RequestStatus } from '../../types';
import { VALID_SUBTYPES } from '../../types';

type MenuAction = {
  key: string;
  label: string;
  to?: string;
  onClick?: () => void;
  tone?: 'danger' | 'success';
};

type RequestViewMode = 'list' | 'kanban';
type KanbanColumnKey = 'pending' | 'in_review' | 'in_progress' | 'finalized';

const FINALIZED_WINDOW_MS = 7 * 24 * 60 * 60 * 1000;

const KANBAN_TARGET_STATUS: Record<KanbanColumnKey, RequestStatus> = {
  pending: 'submitted',
  in_review: 'in_review',
  in_progress: 'in_progress',
  finalized: 'resolved',
};

const NEXT_STATUS_BY_CURRENT: Partial<Record<RequestStatus, RequestStatus>> = {
  submitted: 'in_review',
  in_review: 'in_progress',
  in_progress: 'resolved',
};

function isFinalizedInLast7Days(request: ServiceRequest): boolean {
  if (request.status !== 'resolved' && request.status !== 'rejected') return false;
  const baseDate = request.resolved_at ?? request.updated_at;
  if (!baseDate) return false;
  const ts = new Date(baseDate).getTime();
  if (!Number.isFinite(ts)) return false;
  return Date.now() - ts <= FINALIZED_WINDOW_MS;
}

export default function RequestQueuePage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [page, setPage] = useState(1);
  const [viewMode, setViewMode] = useState<RequestViewMode>('list');
  const [status, setStatus] = useState('');
  const [type, setType] = useState('');
  const [subtype, setSubtype] = useState('');
  const [search, setSearch] = useState('');
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [draggedRequestId, setDraggedRequestId] = useState<string | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<KanbanColumnKey | null>(null);
  const [cfFilters, setCfFilters] = useState<Record<string, string>>({});

  // Employee selection modal state
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [employeeSearch, setEmployeeSearch] = useState('');
  const [showNewEmployeeForm, setShowNewEmployeeForm] = useState(false);
  const [newEmpEmail, setNewEmpEmail] = useState('');
  const [newEmpName, setNewEmpName] = useState('');
  const [newEmpError, setNewEmpError] = useState('');

  const usersQuery = useQuery({
    queryKey: ['request-modal-assignable-users'],
    queryFn: async () => {
      const { data } = await api.get('/assets/assignable-users');
      return data.data as AssignableUser[];
    },
    enabled: showEmployeeModal,
  });

  const filteredEmployees = useMemo(() => {
    const all = usersQuery.data ?? [];
    if (!employeeSearch.trim()) return all;
    const q = employeeSearch.toLowerCase();
    return all.filter(
      (u) => u.email.toLowerCase().includes(q) || (u.name && u.name.toLowerCase().includes(q)),
    );
  }, [usersQuery.data, employeeSearch]);

  const createEmployeeMut = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/users/quick-create', {
        email: newEmpEmail.trim(),
        name: newEmpName.trim() || undefined,
      });
      return data.data as AssignableUser;
    },
    onSuccess: (created) => {
      setNewEmpError('');
      void queryClient.invalidateQueries({ queryKey: ['request-modal-assignable-users'] });
      selectEmployee(created);
    },
    onError: (err: unknown) => {
      setNewEmpError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        || t('page.new_request.error_create'),
      );
    },
  });

  const handleCreateEmployee = () => {
    setNewEmpError('');
    const email = newEmpEmail.trim();
    if (!email) {
      setNewEmpError(t('page.users.error_email_required'));
      return;
    }
    if (!email.includes('@')) {
      setNewEmpError(t('page.vendors.error_email_invalid'));
      return;
    }
    createEmployeeMut.mutate();
  };

  const openEmployeeModal = () => {
    setEmployeeSearch('');
    setShowNewEmployeeForm(false);
    setNewEmpEmail('');
    setNewEmpName('');
    setNewEmpError('');
    setShowEmployeeModal(true);
  };

  const selectEmployee = (u: AssignableUser) => {
    setShowEmployeeModal(false);
    const label = u.name || u.email;
    navigate(`/my/requests/new?on_behalf_of=${u.id}&on_behalf_of_label=${encodeURIComponent(label)}`);
  };

  const handleCfFilterChange = (key: string, value: string) => {
    setCfFilters((prev) => {
      const next = { ...prev };
      if (value) { next[key] = value; } else { delete next[key]; }
      return next;
    });
    setPage(1);
  };

  const listQuery = useQuery({
    queryKey: ['requests', page, status, type, subtype, search, cfFilters],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (status) params.status = status;
      if (type) params.type = type;
      if (subtype) params.subtype = subtype;
      if (search) params.search = search;
      Object.entries(cfFilters).forEach(([k, v]) => { if (v) params[k] = v; });
      const { data } = await api.get('/requests', { params });
      return data as PaginatedResponse<ServiceRequest>;
    },
    enabled: viewMode === 'list',
  });

  const kanbanQuery = useQuery({
    queryKey: ['requests-kanban', type, subtype, search, cfFilters],
    queryFn: async () => {
      const params: Record<string, unknown> = { page: 1, page_size: 100 };
      if (type) params.type = type;
      if (subtype) params.subtype = subtype;
      if (search) params.search = search;
      Object.entries(cfFilters).forEach(([k, v]) => { if (v) params[k] = v; });
      const { data } = await api.get('/requests', { params });
      return data as PaginatedResponse<ServiceRequest>;
    },
    enabled: viewMode === 'kanban',
  });

  const activeData = viewMode === 'list' ? listQuery.data : kanbanQuery.data;
  const activeLoading = viewMode === 'list' ? listQuery.isLoading : kanbanQuery.isLoading;
  const activeError = viewMode === 'list' ? listQuery.isError : kanbanQuery.isError;
  const activeErrorValue = viewMode === 'list' ? listQuery.error : kanbanQuery.error;

  // Stats query
  const { data: statsData } = useQuery({
    queryKey: ['requests-stats'],
    queryFn: async () => {
      const { data } = await api.get('/requests', { params: { page_size: 100 } });
      return data as PaginatedResponse<ServiceRequest>;
    },
    staleTime: 30_000,
  });

  const statsCounts = useMemo(() => {
    const all = statsData?.data ?? [];
    return {
      total: statsData?.meta?.total ?? 0,
      open: all.filter(r => r.status === 'submitted' || r.status === 'in_review' || r.status === 'pending_approval').length,
      in_progress: all.filter(r => r.status === 'in_progress').length,
      resolved: all.filter(r => r.status === 'resolved').length,
      rejected: all.filter(r => r.status === 'rejected').length,
    };
  }, [statsData]);

  // Mutations
  const assignMut = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/requests/${id}/assign`, { assigned_to: user?.id });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['requests'] });
      void queryClient.invalidateQueries({ queryKey: ['requests-kanban'] });
      void queryClient.invalidateQueries({ queryKey: ['requests-stats'] });
      void queryClient.invalidateQueries({ queryKey: ['queue-counts'] });
      void queryClient.invalidateQueries({ queryKey: ['my-task-counts'] });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast({ title: detail || t('page.request_detail.error_generic'), variant: 'error' });
    },
  });

  const statusMut = useMutation({
    mutationFn: async ({ id, newStatus }: { id: string; newStatus: string }) => {
      await api.patch(`/requests/${id}/status`, { status: newStatus });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['requests'] });
      void queryClient.invalidateQueries({ queryKey: ['requests-kanban'] });
      void queryClient.invalidateQueries({ queryKey: ['requests-stats'] });
      void queryClient.invalidateQueries({ queryKey: ['queue-counts'] });
      void queryClient.invalidateQueries({ queryKey: ['my-task-counts'] });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast({ title: detail || t('page.request_detail.error_status_update'), variant: 'error' });
    },
  });

  const mutBusy = assignMut.isPending || statusMut.isPending;

  // Dynamic subtype options based on selected type
  const subtypeOptions = type
    ? (VALID_SUBTYPES[type as keyof typeof VALID_SUBTYPES] ?? [])
    : (Object.values(VALID_SUBTYPES).flat() as string[]);
  const uniqueSubtypes = [...new Set(subtypeOptions)];

  // Build menu actions for a request
  const menuActionsFor = (r: ServiceRequest): MenuAction[] => {
    const actions: MenuAction[] = [
      { key: 'view', label: t('table.details'), to: `/requests/${r.id}` },
    ];

    const isUnassigned = !r.assigned_to;
    const canAssign = ['submitted', 'in_review', 'in_progress'].includes(r.status);

    if (isUnassigned && canAssign) {
      actions.push({
        key: 'assign',
        label: t('page.request_detail.assign_to_me'),
        onClick: () => assignMut.mutate(r.id),
      });
    }

    if (r.status === 'submitted') {
      actions.push({
        key: 'start-review',
        label: t('page.request_queue.action_start_review'),
        onClick: () => statusMut.mutate({ id: r.id, newStatus: 'in_review' }),
      });
    }

    if (r.status === 'in_review') {
      actions.push({
        key: 'start-progress',
        label: t('page.request_queue.action_start_progress'),
        onClick: () => statusMut.mutate({ id: r.id, newStatus: 'in_progress' }),
      });
    }

    if (r.status === 'in_progress') {
      actions.push({
        key: 'resolve',
        label: t('page.request_queue.action_resolve'),
        onClick: () => statusMut.mutate({ id: r.id, newStatus: 'resolved' }),
        tone: 'success',
      });
    }

    if (r.status === 'pending_approval') {
      actions.push({
        key: 'approve',
        label: t('page.request_detail.approve'),
        onClick: () => navigate(`/requests/${r.id}`),
        tone: 'success',
      });
    }

    return actions;
  };

  const kanbanRequests = useMemo(() => kanbanQuery.data?.data ?? [], [kanbanQuery.data]);

  const kanbanColumns = useMemo(() => ([
    {
      key: 'pending' as const,
      title: t('page.request_queue.kanban_pending'),
      items: kanbanRequests.filter((r) => r.status === 'submitted' || r.status === 'pending_approval'),
    },
    {
      key: 'in_review' as const,
      title: t('page.request_queue.kanban_in_review'),
      items: kanbanRequests.filter((r) => r.status === 'in_review'),
    },
    {
      key: 'in_progress' as const,
      title: t('page.request_queue.kanban_in_progress'),
      items: kanbanRequests.filter((r) => r.status === 'in_progress'),
    },
    {
      key: 'finalized' as const,
      title: t('page.request_queue.kanban_finalized_7d'),
      items: kanbanRequests.filter((r) => isFinalizedInLast7Days(r)),
    },
  ]), [kanbanRequests, t]);

  const canAssignRequest = (r: ServiceRequest) => !r.assigned_to && ['submitted', 'in_review', 'in_progress'].includes(r.status);

  const getDraggedRequest = () => kanbanRequests.find((r) => r.id === draggedRequestId);

  const canDropInColumn = (columnKey: KanbanColumnKey): boolean => {
    const request = getDraggedRequest();
    if (!request) return false;
    const nextStatus = NEXT_STATUS_BY_CURRENT[request.status];
    return Boolean(nextStatus && nextStatus === KANBAN_TARGET_STATUS[columnKey]);
  };

  const handleColumnDragOver = (event: DragEvent<HTMLDivElement>, columnKey: KanbanColumnKey) => {
    if (!canDropInColumn(columnKey)) return;
    event.preventDefault();
    if (dragOverColumn !== columnKey) setDragOverColumn(columnKey);
  };

  const handleColumnDrop = (event: DragEvent<HTMLDivElement>, columnKey: KanbanColumnKey) => {
    event.preventDefault();
    const request = getDraggedRequest();
    setDragOverColumn(null);
    setDraggedRequestId(null);
    if (!request) return;
    const nextStatus = NEXT_STATUS_BY_CURRENT[request.status];
    const targetStatus = KANBAN_TARGET_STATUS[columnKey];
    if (!nextStatus || nextStatus !== targetStatus) return;
    statusMut.mutate({ id: request.id, newStatus: targetStatus });
  };

  const statItems = [
    {
      label: t('page.request_queue.stat_total'),
      value: statsCounts.total,
      colorClass: 'text-primary',
      bgClass: 'bg-primary/10',
      icon: <ClipboardList className="h-4 w-4" />,
    },
    {
      label: t('page.request_queue.stat_open'),
      value: statsCounts.open,
      colorClass: 'text-warning-foreground',
      bgClass: 'bg-warning/15',
      icon: <Clock3 className="h-4 w-4" />,
    },
    {
      label: t('page.request_queue.stat_in_progress'),
      value: statsCounts.in_progress,
      colorClass: 'text-primary',
      bgClass: 'bg-primary/10',
      icon: <LoaderCircle className="h-4 w-4" />,
    },
    {
      label: t('page.request_queue.stat_resolved'),
      value: statsCounts.resolved,
      colorClass: 'text-success',
      bgClass: 'bg-success/15',
      icon: <CircleCheck className="h-4 w-4" />,
    },
    {
      label: t('page.request_queue.stat_rejected'),
      value: statsCounts.rejected,
      colorClass: 'text-destructive',
      bgClass: 'bg-destructive/10',
      icon: <CircleX className="h-4 w-4" />,
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {t('page.request_queue.title')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('page.request_queue.subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-md border border-border bg-card p-1">
            <Tooltip content={t('page.request_queue.view_list')}>
              <button
                type="button"
                onClick={() => setViewMode('list')}
                aria-label={t('page.request_queue.view_list')}
                title={t('page.request_queue.view_list')}
                className={`inline-flex h-8 w-8 items-center justify-center rounded-sm transition-colors ${viewMode === 'list' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
              >
                <List className="h-4 w-4" aria-hidden="true" />
              </button>
            </Tooltip>
            <Tooltip content={t('page.request_queue.view_kanban')}>
              <button
                type="button"
                onClick={() => setViewMode('kanban')}
                aria-label={t('page.request_queue.view_kanban')}
                title={t('page.request_queue.view_kanban')}
                className={`inline-flex h-8 w-8 items-center justify-center rounded-sm transition-colors ${viewMode === 'kanban' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
              >
                <Kanban className="h-4 w-4" aria-hidden="true" />
              </button>
            </Tooltip>
          </div>
          <button
            type="button"
            onClick={openEmployeeModal}
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {t('page.request_queue.new')}
          </button>
        </div>
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
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
          <input
            type="search"
            placeholder={t('page.request_queue.search_placeholder')}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 bg-card"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {viewMode === 'list' && (
            <select
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}
              className="w-[150px] bg-card"
            >
              <option value="">{t('page.request_queue.all_statuses')}</option>
              <option value="pending_approval">{t('enum.pending_approval')}</option>
              <option value="submitted">{t('enum.submitted')}</option>
              <option value="in_review">{t('enum.in_review')}</option>
              <option value="in_progress">{t('enum.in_progress')}</option>
              <option value="resolved">{t('enum.resolved')}</option>
              <option value="rejected">{t('enum.rejected')}</option>
            </select>
          )}
          <select
            value={type}
            onChange={(e) => { setType(e.target.value); setSubtype(''); setPage(1); }}
            className="w-[150px] bg-card"
          >
            <option value="">{t('page.request_queue.all_types')}</option>
            <option value="incident">{t('enum.incident')}</option>
            <option value="new_equipment">{t('enum.new_equipment')}</option>
            <option value="onboarding">{t('enum.onboarding')}</option>
            <option value="repair">{t('enum.repair')}</option>
            <option value="configuration">{t('enum.configuration')}</option>
            <option value="access_request">{t('enum.access_request')}</option>
          </select>
          {uniqueSubtypes.length > 0 && (
            <select
              value={subtype}
              onChange={(e) => { setSubtype(e.target.value); setPage(1); }}
              className="w-[150px] bg-card"
            >
              <option value="">{t('page.request_queue.all_subtypes')}</option>
              {uniqueSubtypes.map((s) => (
                <option key={s} value={s}>{t(`enum.${s}`)}</option>
              ))}
            </select>
          )}
        </div>
      </div>
      <CustomFieldFilters entityType="request" filters={cfFilters} onFilterChange={handleCfFilterChange} />

      {/* Content */}
      {activeLoading ? <Loading /> : activeError ? (
        <ErrorState
          message={(activeErrorValue as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
          onRetry={() => { void (viewMode === 'list' ? listQuery.refetch() : kanbanQuery.refetch()); }}
        />
      ) : !activeData?.data.length ? (
        <EmptyState message={t('page.request_queue.empty')} />
      ) : (
        <>
          {viewMode === 'list' ? (
            <>
              <Table>
                <thead>
                  <tr className="hover:bg-transparent">
                    <Th className="pl-4">{t('table.title')}</Th>
                    <Th>{t('table.type')}</Th>
                    <Th>{t('table.priority')}</Th>
                    <Th>{t('table.status')}</Th>
                    <Th className="hidden md:table-cell">{t('table.assigned_to')}</Th>
                    <Th className="hidden sm:table-cell">{t('table.created')}</Th>
                    <Th className="w-12 pr-4">
                      <span className="sr-only">{t('table.actions')}</span>
                    </Th>
                  </tr>
                </thead>
                <tbody>
                  {(listQuery.data?.data ?? []).map((r) => {
                    const actions = menuActionsFor(r);
                    return (
                      <Tr key={r.id}>
                        <Td className="pl-4">
                          <Link
                            to={`/requests/${r.id}`}
                            className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                          >
                            {r.title}
                          </Link>
                          <p className="text-xs text-muted-foreground">
                            {r.created_by_name || r.created_by_email}
                            {r.created_by_name && r.created_by_email && (
                              <span className="ml-1 text-muted-foreground/60">({r.created_by_email})</span>
                            )}
                          </p>
                        </Td>
                        <Td>
                          <div className="flex items-center gap-1.5">
                            <WorkflowIcon name={r.workflow_template_icon} className="h-4 w-4 shrink-0 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">{r.workflow_template_name || t(`enum.${r.type}`)}</span>
                            {r.subtype && <span className="text-xs text-muted-foreground">({t(`enum.${r.subtype}`)})</span>}
                          </div>
                        </Td>
                        <Td><StatusBadge status={r.priority} /></Td>
                        <Td><StatusBadge status={r.status} /></Td>
                        <Td className="hidden md:table-cell">
                          <span className="text-sm text-muted-foreground">{r.assigned_to_name || r.assigned_to_email || '—'}</span>
                        </Td>
                        <Td className="hidden sm:table-cell">
                          <span className="text-sm text-muted-foreground">{formatDate(r.created_at)}</span>
                        </Td>
                        <td className="px-4 py-3 text-sm">
                          <div className="flex items-center justify-end gap-2">
                            <Tooltip content={t('table.details')}>
                              <Link
                                to={`/requests/${r.id}`}
                                aria-label={t('table.details')}
                                className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                              >
                                <Eye className="h-4 w-4" />
                              </Link>
                            </Tooltip>

                            {actions.length > 1 && (
                              <div className="relative">
                                <Tooltip content={t('page.request_queue.more_actions')}>
                                  <button
                                    type="button"
                                    className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                                    aria-label={t('page.request_queue.more_actions')}
                                    onClick={() => setOpenMenuId((cur) => (cur === r.id ? null : r.id))}
                                  >
                                    <EllipsisVertical className="h-4 w-4" aria-hidden="true" />
                                  </button>
                                </Tooltip>
                                {openMenuId === r.id && (
                                  <div className="absolute right-0 z-20 mt-2 min-w-[180px] rounded-lg border border-border bg-card p-1 shadow-lg">
                                    <button
                                      type="button"
                                      className="block w-full rounded-md px-3 py-2 text-left text-xs text-muted-foreground hover:bg-accent"
                                      onClick={() => setOpenMenuId(null)}
                                    >
                                      {t('common.close')}
                                    </button>
                                    {actions.filter(a => a.key !== 'view').map((action) => (
                                      action.to ? (
                                        <Link
                                          key={action.key}
                                          to={action.to}
                                          className={`block rounded-md px-3 py-2 text-left text-xs hover:bg-accent ${action.tone === 'danger' ? 'text-destructive' : action.tone === 'success' ? 'text-success' : 'text-foreground'}`}
                                          onClick={() => setOpenMenuId(null)}
                                        >
                                          {action.label}
                                        </Link>
                                      ) : (
                                        <button
                                          key={action.key}
                                          type="button"
                                          disabled={mutBusy}
                                          onClick={() => { action.onClick?.(); setOpenMenuId(null); }}
                                          className={`block w-full rounded-md px-3 py-2 text-left text-xs hover:bg-accent disabled:opacity-50 ${action.tone === 'danger' ? 'text-destructive' : action.tone === 'success' ? 'text-success' : 'text-foreground'}`}
                                        >
                                          {action.label}
                                        </button>
                                      )
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </td>
                      </Tr>
                    );
                  })}
                </tbody>
              </Table>
              <Pagination page={page} pageSize={20} total={listQuery.data?.meta.total ?? 0} onChange={setPage} />
            </>
          ) : (
            <div className="space-y-3">
              <p className="text-xs text-muted-foreground">
                {t('page.request_queue.kanban_drag_hint')}
              </p>
              <div className="grid gap-4 xl:grid-cols-4">
                {kanbanColumns.map((column) => (
                  <div
                    key={column.key}
                    onDragOver={(event) => handleColumnDragOver(event, column.key)}
                    onDrop={(event) => handleColumnDrop(event, column.key)}
                    onDragLeave={() => {
                      if (dragOverColumn === column.key) setDragOverColumn(null);
                    }}
                    className={`rounded-lg border bg-card ${dragOverColumn === column.key ? 'border-primary ring-1 ring-primary/30' : 'border-border'}`}
                  >
                    <div className="flex items-center justify-between border-b border-border px-3 py-2">
                      <h3 className="text-sm font-medium text-foreground">{column.title}</h3>
                      <span className="rounded-full bg-secondary px-2 py-0.5 text-xs text-muted-foreground">
                        {column.items.length}
                      </span>
                    </div>
                    <div className="min-h-[260px] space-y-2 p-3">
                      {column.items.map((r) => {
                        const canDrag = Boolean(NEXT_STATUS_BY_CURRENT[r.status]) && !mutBusy;
                        return (
                          <article
                            key={r.id}
                            draggable={canDrag}
                            onDragStart={() => setDraggedRequestId(r.id)}
                            onDragEnd={() => { setDraggedRequestId(null); setDragOverColumn(null); }}
                            className={`rounded-lg border border-border bg-background p-3 ${canDrag ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'}`}
                          >
                            <Link
                              to={`/requests/${r.id}`}
                              className="line-clamp-2 text-sm font-medium text-foreground hover:text-primary transition-colors"
                            >
                              {r.title}
                            </Link>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {r.created_by_name || r.created_by_email}
                            </p>
                            <div className="mt-1.5 flex items-center gap-1 text-xs text-muted-foreground">
                              <WorkflowIcon name={r.workflow_template_icon} className="h-3 w-3 shrink-0" />
                              <span>{r.workflow_template_name || t(`enum.${r.type}`)}</span>
                            </div>
                            <div className="mt-2 flex flex-wrap gap-1.5">
                              <StatusBadge status={r.priority} />
                              <StatusBadge status={r.status} />
                            </div>
                            <div className="mt-2 text-xs text-muted-foreground">
                              {formatDate(r.created_at)}
                            </div>
                            <div className="mt-3 flex items-center gap-3 text-xs">
                              <Link to={`/requests/${r.id}`} className="font-medium text-primary hover:underline">
                                {t('table.details')}
                              </Link>
                              {canAssignRequest(r) && (
                                <button
                                  type="button"
                                  disabled={mutBusy}
                                  onClick={() => assignMut.mutate(r.id)}
                                  className="font-medium text-muted-foreground hover:text-foreground disabled:opacity-50"
                                >
                                  {t('page.request_detail.assign_to_me')}
                                </button>
                              )}
                            </div>
                          </article>
                        );
                      })}
                      {column.items.length === 0 && (
                        <div className="rounded-lg border border-dashed border-border px-3 py-6 text-center text-xs text-muted-foreground">
                          {t('page.request_queue.empty')}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Employee selection modal */}
      {showEmployeeModal && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => setShowEmployeeModal(false)}
            aria-label={t('common.close')}
          />
          <div className="relative z-[91] w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">
              {t('page.request_queue.select_employee')}
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {t('page.request_queue.select_employee_desc')}
            </p>

            {/* New Employee toggle */}
            {!showNewEmployeeForm ? (
              <button
                type="button"
                onClick={() => setShowNewEmployeeForm(true)}
                className="mt-4 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
              >
                {t('page.request_queue.new_employee')}
              </button>
            ) : (
              <div className="mt-4 rounded-lg border border-border bg-muted/30 p-3 space-y-2">
                {newEmpError && (
                  <div className="flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                    <CircleAlert className="h-4 w-4 shrink-0" />
                    {newEmpError}
                  </div>
                )}
                <div className="flex items-end gap-2">
                  <div className="flex-1 space-y-2">
                    <input
                      type="email"
                      value={newEmpEmail}
                      onChange={(e) => { setNewEmpEmail(e.target.value); setNewEmpError(''); }}
                      placeholder="email@company.com"
                      className="w-full text-sm"
                    />
                    <input
                      type="text"
                      value={newEmpName}
                      onChange={(e) => setNewEmpName(e.target.value)}
                      placeholder={t('table.name')}
                      className="w-full text-sm"
                    />
                  </div>
                  <button
                    type="button"
                    disabled={createEmployeeMut.isPending}
                    onClick={handleCreateEmployee}
                    className="shrink-0 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all"
                  >
                    {createEmployeeMut.isPending ? t('page.request_queue.creating_employee') : t('page.request_queue.create_employee')}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setShowNewEmployeeForm(false); setNewEmpEmail(''); setNewEmpName(''); setNewEmpError(''); }}
                    className="shrink-0 rounded-md border border-border bg-card px-3 py-2 text-sm font-medium text-foreground hover:bg-accent transition-all"
                  >
                    {t('common.cancel')}
                  </button>
                </div>
              </div>
            )}

            {/* Search */}
            <div className="mt-4">
              <input
                type="search"
                value={employeeSearch}
                onChange={(e) => setEmployeeSearch(e.target.value)}
                placeholder={t('page.request_queue.search_employee')}
                className="w-full"
              />
            </div>

            {/* User list */}
            <div className="mt-3 max-h-72 overflow-auto rounded-lg border border-border">
              {usersQuery.isLoading ? (
                <p className="px-4 py-3 text-sm text-muted-foreground">{t('common.loading')}</p>
              ) : filteredEmployees.length === 0 ? (
                <p className="px-4 py-3 text-sm text-muted-foreground">{t('page.request_queue.no_employee_match')}</p>
              ) : (
                filteredEmployees.map((u) => (
                  <button
                    key={u.id}
                    type="button"
                    onClick={() => selectEmployee(u)}
                    className="flex w-full items-center justify-between border-b border-border/50 px-4 py-2.5 text-left text-sm text-foreground hover:bg-accent last:border-b-0"
                  >
                    <span className="truncate font-medium">{u.name || u.email}</span>
                    <span className="ml-3 text-xs text-muted-foreground">{u.email}</span>
                  </button>
                ))
              )}
            </div>

            {/* Cancel */}
            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={() => setShowEmployeeModal(false)}
                className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground shadow-sm hover:bg-accent transition-all"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
