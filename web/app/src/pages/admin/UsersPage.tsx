import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Badge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { User, Department, PaginatedResponse } from '../../types';

export default function UsersPage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [pendingDeactivate, setPendingDeactivate] = useState<{ id: string; email: string } | null>(null);
  const queryClient = useQueryClient();
  const { showToast } = useToast();

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
      const { data } = await api.get('/departments', { params: { page: 1, page_size: 200 } });
      return data.data as Department[];
    },
  });

  const departmentOptions = useMemo(() => departments ?? [], [departments]);

  const [roleError, setRoleError] = useState('');

  const inviteUser = useMutation({
    mutationFn: () => api.post('/users/invite', { email: inviteEmail }),
    onSuccess: () => {
      setInviteEmail('');
      setShowInvite(false);
      queryClient.invalidateQueries({ queryKey: ['users'] });
      showToast({ title: t('page.users.toast_invitation_sent'), description: t('page.users.toast_invitation_desc'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.users.error_invite');
      showToast({ title: t('page.users.error_invite_title'), description: msg, variant: 'error' });
    },
  });

  const changeRole = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      api.patch(`/users/${userId}/role`, { role }),
    onSuccess: () => {
      setRoleError('');
      queryClient.invalidateQueries({ queryKey: ['users'] });
      showToast({ title: t('page.users.toast_role_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.users.error_role');
      setRoleError(msg);
      showToast({ title: t('page.users.error_role_title'), description: msg, variant: 'error' });
    },
  });

  const assignDepartment = useMutation({
    mutationFn: ({ userId, departmentId }: { userId: string; departmentId: string | null }) =>
      api.patch(`/users/${userId}/department`, { department_id: departmentId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      showToast({ title: t('page.users.toast_department_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.users.error_update');
      showToast({ title: t('page.users.error_department_title'), description: msg, variant: 'error' });
    },
  });

  const toggleActive = useMutation({
    mutationFn: ({ userId, active }: { userId: string; active: boolean }) =>
      api.patch(`/users/${userId}/${active ? 'activate' : 'deactivate'}`),
    onSuccess: (_res, vars) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
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

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-xl font-bold text-gray-900">{t('page.users.title')}</h2>
        <button onClick={() => setShowInvite((v) => !v)} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
          {showInvite ? t('common.cancel') : t('page.users.invite_user')}
        </button>
      </div>

      {showInvite && (
        <Card className="mb-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              inviteUser.mutate();
            }}
            className="flex items-end gap-3"
          >
            <div className="flex-1">
              <label className="mb-1 block text-sm font-medium text-gray-700">{t('table.email')}</label>
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder={t('common.placeholder_user_email')}
                required
                className="w-full rounded-lg border px-3 py-2 text-sm"
              />
            </div>
            <button
              type="submit"
              disabled={inviteUser.isPending || !inviteEmail.trim()}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {inviteUser.isPending ? t('auth.login.sending') : t('page.users.send_invite')}
            </button>
          </form>
        </Card>
      )}

      <Card>
        <div className="mb-4 flex gap-3">
          <input placeholder={t('common.search')} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="w-48 rounded-lg border px-3 py-1.5 text-sm" />
          <select value={roleFilter} onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }} className="rounded-lg border px-3 py-1.5 text-sm">
            <option value="">{t('page.users.all_roles')}</option>
            {['employee', 'technician', 'admin'].map((r) => <option key={r} value={r}>{t(`enum.${r}`)}</option>)}
          </select>
        </div>

        {roleError && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {roleError}
          </div>
        )}

        {isLoading ? <Loading /> : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => {
              void refetch();
            }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.users.empty')} />
        ) : (
          <>
            <Table>
              <thead><tr><Th>{t('table.email')}</Th><Th>{t('table.role')}</Th><Th>{t('table.department')}</Th><Th>{t('table.status')}</Th><Th>{t('table.actions')}</Th></tr></thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((u) => (
                  <tr key={u.id}>
                    <Td>{u.email}</Td>
                    <Td>
                      <select
                        value={u.role}
                        onChange={(e) => changeRole.mutate({ userId: u.id, role: e.target.value })}
                        className="rounded border px-2 py-1 text-xs"
                      >
                        {['employee', 'technician', 'admin'].map((r) => <option key={r} value={r}>{t(`enum.${r}`)}</option>)}
                      </select>
                    </Td>
                    <Td>
                      <select
                        value={u.department_id ?? ''}
                        onChange={(e) => assignDepartment.mutate({ userId: u.id, departmentId: e.target.value || null })}
                        className="max-w-40 rounded border px-2 py-1 text-xs"
                      >
                        <option value="">{t('common.unassigned')}</option>
                        {departmentOptions.map((d) => (
                          <option key={d.id} value={d.id}>{d.name}</option>
                        ))}
                      </select>
                    </Td>
                    <Td>{u.is_active ? <Badge variant="success">{t('page.users.active')}</Badge> : <Badge variant="danger">{t('page.users.inactive')}</Badge>}</Td>
                    <Td>
                      <button
                        onClick={() => {
                          if (u.is_active) {
                            setPendingDeactivate({ id: u.id, email: u.email });
                          } else {
                            toggleActive.mutate({ userId: u.id, active: true });
                          }
                        }}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        {u.is_active ? t('page.users.deactivate') : t('page.users.activate')}
                      </button>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </>
        )}
      </Card>

      <ConfirmDialog
        open={Boolean(pendingDeactivate)}
        title={t('page.users.deactivate_user')}
        description={pendingDeactivate ? t('page.users.deactivate_desc', { email: pendingDeactivate.email }) : ''}
        confirmLabel={t('page.users.deactivate')}
        tone="danger"
        busy={toggleActive.isPending}
        onCancel={() => setPendingDeactivate(null)}
        onConfirm={() => {
          if (pendingDeactivate) {
            toggleActive.mutate({ userId: pendingDeactivate.id, active: false }, {
              onSettled: () => setPendingDeactivate(null),
            });
          }
        }}
      />
    </div>
  );
}
