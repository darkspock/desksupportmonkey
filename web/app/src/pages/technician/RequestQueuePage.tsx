import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Pagination } from '../../components/ui/Pagination';
import { Tooltip } from '../../components/ui/Tooltip';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { ServiceRequest, PaginatedResponse, AssignableUser } from '../../types';
import { VALID_SUBTYPES } from '../../types';

type MenuAction = {
  key: string;
  label: string;
  to?: string;
  onClick?: () => void;
  tone?: 'danger' | 'success';
};

export default function RequestQueuePage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [type, setType] = useState('');
  const [subtype, setSubtype] = useState('');
  const [search, setSearch] = useState('');
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

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

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['requests', page, status, type, subtype, search],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (status) params.status = status;
      if (type) params.type = type;
      if (subtype) params.subtype = subtype;
      if (search) params.search = search;
      const { data } = await api.get('/requests', { params });
      return data as PaginatedResponse<ServiceRequest>;
    },
  });

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
      void queryClient.invalidateQueries({ queryKey: ['requests-stats'] });
    },
  });

  const statusMut = useMutation({
    mutationFn: async ({ id, newStatus }: { id: string; newStatus: string }) => {
      await api.put(`/requests/${id}/status`, { status: newStatus });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['requests'] });
      void queryClient.invalidateQueries({ queryKey: ['requests-stats'] });
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

  const statItems = [
    {
      label: t('page.request_queue.stat_total'),
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
      label: t('page.request_queue.stat_open'),
      value: statsCounts.open,
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
      label: t('page.request_queue.stat_in_progress'),
      value: statsCounts.in_progress,
      colorClass: 'text-primary',
      bgClass: 'bg-primary/10',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
      ),
    },
    {
      label: t('page.request_queue.stat_resolved'),
      value: statsCounts.resolved,
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
      label: t('page.request_queue.stat_rejected'),
      value: statsCounts.rejected,
      colorClass: 'text-destructive',
      bgClass: 'bg-destructive/10',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="m15 9-6 6M9 9l6 6" />
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
            {t('page.request_queue.title')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('page.request_queue.subtitle')}
          </p>
        </div>
        <button
          type="button"
          onClick={openEmployeeModal}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {t('page.request_queue.new')}
        </button>
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
            placeholder={t('page.request_queue.search_placeholder')}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 bg-card"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
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

      {/* Table */}
      {isLoading ? <Loading /> : isError ? (
        <ErrorState
          message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
          onRetry={() => { void refetch(); }}
        />
      ) : !data?.data.length ? (
        <EmptyState message={t('page.request_queue.empty')} />
      ) : (
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
              {data.data.map((r) => {
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
                      <span className="text-sm text-muted-foreground">{t(`enum.${r.type}`)}</span>
                      {r.subtype && <span className="ml-1 text-xs text-muted-foreground">({t(`enum.${r.subtype}`)})</span>}
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
                        {/* Primary: view detail */}
                        <Tooltip content={t('table.details')}>
                          <Link
                            to={`/requests/${r.id}`}
                            aria-label={t('table.details')}
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                          >
                            {/* Eye icon */}
                            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                              <circle cx="12" cy="12" r="3" />
                            </svg>
                          </Link>
                        </Tooltip>

                        {/* Dots menu */}
                        {actions.length > 1 && (
                          <div className="relative">
                            <Tooltip content={t('page.request_queue.more_actions')}>
                              <button
                                type="button"
                                className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                                aria-label={t('page.request_queue.more_actions')}
                                onClick={() => setOpenMenuId((cur) => (cur === r.id ? null : r.id))}
                              >
                                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor" aria-hidden="true">
                                  <circle cx="12" cy="5" r="2" />
                                  <circle cx="12" cy="12" r="2" />
                                  <circle cx="12" cy="19" r="2" />
                                </svg>
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
          <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
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
                    <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <path d="M12 8v4M12 16h.01" />
                    </svg>
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
