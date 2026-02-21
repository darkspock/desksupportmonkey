import { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Badge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Tooltip } from '../../components/ui/Tooltip';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { User, UserRole, Department, PaginatedResponse } from '../../types';

interface EditModalState {
  userId: string;
  email: string;
  name: string;
  role: UserRole;
  departmentId: string;
}

interface StatusConfirmState {
  userId: string;
  email: string;
  active: boolean;
}

const ROLE_OPTIONS: UserRole[] = ['employee', 'technician', 'admin'];

export default function UsersPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteName, setInviteName] = useState('');
  const [inviteRole, setInviteRole] = useState('employee');
  const [inviteError, setInviteError] = useState('');
  const [editModal, setEditModal] = useState<EditModalState | null>(null);
  const [editError, setEditError] = useState('');
  const [pendingStatusChange, setPendingStatusChange] = useState<StatusConfirmState | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['users', page, search, roleFilter],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;
      const { data } = await api.get('/users', { params });
      return data as PaginatedResponse<User>;
    },
  });

  const { data: departments } = useQuery({
    queryKey: ['users-departments-options'],
    queryFn: async () => {
      const { data } = await api.get('/departments', { params: { page: 1, page_size: 100 } });
      return data.data as Department[];
    },
  });

  const departmentOptions = useMemo(() => departments ?? [], [departments]);
  const departmentNameById = useMemo(
    () => new Map((departmentOptions ?? []).map((d) => [d.id, d.name])),
    [departmentOptions],
  );

  const inviteUser = useMutation({
    mutationFn: ({ email, name, role }: { email: string; name: string; role: string }) =>
      api.post('/users/invite', { email, name: name || undefined, role }),
    onSuccess: () => {
      setInviteEmail('');
      setInviteName('');
      setInviteRole('employee');
      setInviteError('');
      setShowInviteModal(false);
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['asset-assignable-users'] });
      showToast({ title: t('page.users.toast_invitation_sent'), description: t('page.users.toast_invitation_desc'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.users.error_invite');
      setInviteError(msg);
      showToast({ title: t('page.users.error_invite_title'), description: msg, variant: 'error' });
    },
  });

  const saveEdit = useMutation({
    mutationFn: async (payload: EditModalState) => {
      await api.patch(`/users/${payload.userId}`, {
        name: payload.name || null,
        role: payload.role,
        department_id: payload.departmentId || null,
      });
    },
    onSuccess: () => {
      setEditError('');
      setEditModal(null);
      queryClient.invalidateQueries({ queryKey: ['users'] });
      showToast({ title: t('page.users.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.users.error_role');
      setEditError(msg);
      showToast({ title: t('page.users.error_update_title'), description: msg, variant: 'error' });
    },
  });

  const toggleActive = useMutation({
    mutationFn: ({ userId, active }: { userId: string; active: boolean }) =>
      api.patch(`/users/${userId}/${active ? 'activate' : 'deactivate'}`),
    onSuccess: (_res, vars) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setPendingStatusChange(null);
      showToast({
        title: vars.active ? t('page.users.toast_user_activated') : t('page.users.toast_user_deactivated'),
        variant: 'success',
      });
    },
    onError: (err: unknown, vars) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.users.error_update');
      showToast({
        title: vars.active ? t('page.users.error_activate_title') : t('page.users.error_deactivate_title'),
        description: msg,
        variant: 'error',
      });
    },
  });

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (pendingStatusChange && !toggleActive.isPending) {
        setPendingStatusChange(null);
        return;
      }
      if (editModal && !saveEdit.isPending) {
        setEditModal(null);
        setEditError('');
        return;
      }
      if (showInviteModal && !inviteUser.isPending) {
        setShowInviteModal(false);
        setInviteEmail('');
        setInviteName('');
        setInviteRole('employee');
        setInviteError('');
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [
    editModal,
    saveEdit.isPending,
    inviteUser.isPending,
    pendingStatusChange,
    showInviteModal,
    toggleActive.isPending,
  ]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.users.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.users.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setInviteEmail('');
            setInviteName('');
            setInviteRole('employee');
            setInviteError('');
            setShowInviteModal(true);
          }}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {t('page.users.invite_user')}
        </button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <svg
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
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
            placeholder={t('page.users.search_placeholder')}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full bg-card pl-9"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <select value={roleFilter} onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }} className="w-[150px] bg-card">
            <option value="">{t('page.users.all_roles')}</option>
            {ROLE_OPTIONS.map((r) => <option key={r} value={r}>{t(`enum.${r}`)}</option>)}
          </select>
        </div>
      </div>

      {isLoading ? <Loading /> : isError ? (
        <ErrorState
          message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
          onRetry={() => {
            void refetch();
          }}
        />
      ) : !data?.data.length ? (
        <EmptyState
          message={t('page.users.empty')}
          action={(
            <button
              type="button"
              onClick={() => {
                setInviteEmail('');
                setInviteRole('employee');
                setInviteError('');
                setShowInviteModal(true);
              }}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
            >
              {t('page.users.invite_user')}
            </button>
          )}
        />
      ) : (
        <>
          <Table>
            <thead>
              <tr className="hover:bg-transparent">
                <Th className="pl-4">{t('table.email')}</Th>
                <Th>{t('table.name')}</Th>
                <Th>{t('table.role')}</Th>
                <Th className="hidden md:table-cell">{t('table.department')}</Th>
                <Th>{t('table.status')}</Th>
                <Th className="pr-4 text-right">{t('table.actions')}</Th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((u) => (
                <Tr key={u.id}>
                  <Td className="pl-4">
                    <span className="text-sm font-medium text-foreground">{u.email}</span>
                  </Td>
                  <Td><span className="text-sm text-foreground">{u.name || '—'}</span></Td>
                  <Td>{t(`enum.${u.role}`)}</Td>
                  <Td className="hidden md:table-cell">{u.department_id ? (departmentNameById.get(u.department_id) ?? t('common.unassigned')) : t('common.unassigned')}</Td>
                  <Td>{u.is_active ? <Badge variant="success">{t('page.users.active')}</Badge> : <Badge variant="danger">{t('page.users.inactive')}</Badge>}</Td>
                  <Td className="pr-4">
                    <div className="flex items-center justify-end gap-2">
                      <Tooltip content={t('common.edit')}>
                        <button
                          type="button"
                          onClick={() => {
                            setEditError('');
                            setEditModal({
                              userId: u.id,
                              email: u.email,
                              name: u.name || '',
                              role: u.role,
                              departmentId: u.department_id ?? '',
                            });
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
                      <Tooltip content={u.is_active ? t('page.users.deactivate') : t('page.users.activate')}>
                        <button
                          type="button"
                          onClick={() => setPendingStatusChange({ userId: u.id, email: u.email, active: !u.is_active })}
                          aria-label={u.is_active ? t('page.users.deactivate') : t('page.users.activate')}
                          className={u.is_active
                            ? 'inline-flex h-8 w-8 items-center justify-center rounded-md border border-destructive/40 text-destructive hover:bg-destructive/10 transition-colors'
                            : 'inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors'}
                        >
                          {u.is_active ? (
                            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                              <circle cx="12" cy="12" r="10" />
                              <path d="m4.9 4.9 14.2 14.2" />
                            </svg>
                          ) : (
                            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                              <path d="m9 11 3 3L22 4" />
                            </svg>
                          )}
                        </button>
                      </Tooltip>
                    </div>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
          <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
        </>
      )}

      <ConfirmDialog
        open={Boolean(pendingStatusChange)}
        title={pendingStatusChange?.active ? t('page.users.activate_user') : t('page.users.deactivate_user')}
        description={pendingStatusChange
          ? (
            pendingStatusChange.active
              ? t('page.users.activate_desc', { email: pendingStatusChange.email })
              : t('page.users.deactivate_desc', { email: pendingStatusChange.email })
          )
          : ''}
        confirmLabel={pendingStatusChange?.active ? t('page.users.activate') : t('page.users.deactivate')}
        tone={pendingStatusChange?.active ? 'default' : 'danger'}
        busy={toggleActive.isPending}
        onCancel={() => setPendingStatusChange(null)}
        onConfirm={() => {
          if (pendingStatusChange) {
            toggleActive.mutate({ userId: pendingStatusChange.userId, active: pendingStatusChange.active });
          }
        }}
      />

      {showInviteModal && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (inviteUser.isPending) return;
              setShowInviteModal(false);
              setInviteEmail('');
              setInviteRole('employee');
              setInviteError('');
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.users.invite_user')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const email = inviteEmail.trim();
                if (!email) {
                  setInviteError(t('page.users.error_email_required'));
                  return;
                }
                setInviteError('');
                inviteUser.mutate({ email, name: inviteName.trim(), role: inviteRole });
              }}
              className="mt-4 space-y-4"
            >
              <div>
                {inviteError && <p className="mb-2 text-sm text-destructive">{inviteError}</p>}
                <label className="mb-1.5 block text-muted-foreground">{t('table.email')}</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder={t('common.placeholder_user_email')}
                  required
                  autoFocus
                  className="w-full bg-card"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('table.name')}</label>
                <input
                  type="text"
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                  placeholder={t('common.placeholder_name')}
                  className="w-full bg-card"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('table.role')}</label>
                <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)} className="w-full bg-card">
                  {['employee', 'technician', 'admin'].map((r) => <option key={r} value={r}>{t(`enum.${r}`)}</option>)}
                </select>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (inviteUser.isPending) return;
                    setShowInviteModal(false);
                    setInviteEmail('');
                    setInviteName('');
                    setInviteRole('employee');
                    setInviteError('');
                  }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={inviteUser.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {inviteUser.isPending ? t('auth.login.sending') : t('page.users.send_invite')}
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
              if (!saveEdit.isPending) {
                setEditModal(null);
                setEditError('');
              }
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('common.edit')}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{editModal.email}</p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!editModal.role) {
                  setEditError(t('page.users.error_role_required'));
                  return;
                }
                setEditError('');
                saveEdit.mutate(editModal);
              }}
              className="mt-4 space-y-4"
            >
              <div>
                {editError && <p className="mb-2 text-sm text-destructive">{editError}</p>}
                <label className="mb-1.5 block text-muted-foreground">{t('table.name')}</label>
                <input
                  type="text"
                  value={editModal.name}
                  onChange={(e) => setEditModal({ ...editModal, name: e.target.value })}
                  placeholder={t('common.placeholder_name')}
                  className="w-full bg-card"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('table.role')}</label>
                <select
                  value={editModal.role}
                  onChange={(e) => setEditModal({ ...editModal, role: e.target.value as UserRole })}
                  className="w-full bg-card"
                >
                  {ROLE_OPTIONS.map((r) => <option key={r} value={r}>{t(`enum.${r}`)}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('table.department')}</label>
                <select
                  value={editModal.departmentId}
                  onChange={(e) => setEditModal({ ...editModal, departmentId: e.target.value })}
                  className="w-full bg-card"
                >
                  <option value="">{t('common.unassigned')}</option>
                  {departmentOptions.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (!saveEdit.isPending) {
                      setEditModal(null);
                      setEditError('');
                    }
                  }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={saveEdit.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
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
