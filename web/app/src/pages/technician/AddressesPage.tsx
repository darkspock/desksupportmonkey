import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Table, Th, Td } from '../../components/ui/Table';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { ShippingAddress, PaginatedResponse, AssignableUser } from '../../types';

interface AddressForm {
  label: string;
  street_line_1: string;
  street_line_2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  recipient_name: string;
  phone: string;
  user_id: string;
  is_office: boolean;
}

const emptyForm: AddressForm = {
  label: '', street_line_1: '', street_line_2: '', city: '', state: '',
  postal_code: '', country: 'US', recipient_name: '', phone: '', user_id: '', is_office: false,
};

export default function AddressesPage() {
  const [searchParams] = useSearchParams();
  const createMode = searchParams.get('mode');
  const preselectedUserId = searchParams.get('user_id') ?? '';
  const startsInEmployeeCreate = createMode === 'employee';
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState('');
  const [showForm, setShowForm] = useState(startsInEmployeeCreate);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<AddressForm>(
    startsInEmployeeCreate
      ? { ...emptyForm, is_office: false, user_id: preselectedUserId }
      : emptyForm,
  );
  const [formError, setFormError] = useState('');
  const [deactivateId, setDeactivateId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { t } = useI18n();

  const params: Record<string, string | number | boolean> = { page, page_size: 20 };
  if (typeFilter === 'office') params.is_office = true;
  if (typeFilter === 'employee') params.is_office = false;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['addresses', page, typeFilter],
    queryFn: async () => {
      const { data } = await api.get('/addresses', { params });
      return data as PaginatedResponse<ShippingAddress>;
    },
  });

  const { data: users, isLoading: usersLoading, isError: usersError, refetch: refetchUsers } = useQuery({
    queryKey: ['address-users'],
    queryFn: async () => {
      const { data } = await api.get('/assets/assignable-users');
      return data.data as AssignableUser[];
    },
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['addresses'] });

  const createAddress = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        label: form.label,
        street_line_1: form.street_line_1,
        city: form.city,
        state: form.state,
        postal_code: form.postal_code,
        country: form.country || 'US',
        is_office: form.is_office,
      };
      if (form.street_line_2) payload.street_line_2 = form.street_line_2;
      if (form.recipient_name) payload.recipient_name = form.recipient_name;
      if (form.phone) payload.phone = form.phone;
      if (form.user_id) payload.user_id = form.user_id;
      await api.post('/addresses', payload);
    },
    onSuccess: () => {
      invalidate();
      setShowForm(false);
      setFormError('');
      setForm(emptyForm);
      showToast({ title: t('page.addresses.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.addresses.error_create');
      setFormError(detail);
      showToast({ title: t('page.addresses.error_generic'), description: detail, variant: 'error' });
    },
  });

  const updateAddress = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        label: form.label,
        street_line_1: form.street_line_1,
        city: form.city,
        state: form.state,
        postal_code: form.postal_code,
        country: form.country,
        is_office: form.is_office,
      };
      if (form.street_line_2) payload.street_line_2 = form.street_line_2;
      if (form.recipient_name) payload.recipient_name = form.recipient_name;
      if (form.phone) payload.phone = form.phone;
      if (form.user_id) payload.user_id = form.user_id;
      await api.put(`/addresses/${editingId}`, payload);
    },
    onSuccess: () => {
      invalidate();
      setEditingId(null);
      setShowForm(false);
      setFormError('');
      setForm(emptyForm);
      showToast({ title: t('page.addresses.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.addresses.error_update');
      setFormError(detail);
      showToast({ title: t('page.addresses.error_generic'), description: detail, variant: 'error' });
    },
  });

  const deactivateAddress = useMutation({
    mutationFn: async (addressId: string) => {
      await api.delete(`/addresses/${addressId}`);
    },
    onSuccess: () => {
      invalidate();
      setDeactivateId(null);
      showToast({ title: t('page.addresses.toast_deactivated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.addresses.error_deactivate');
      showToast({ title: t('page.addresses.error_generic'), description: detail, variant: 'error' });
    },
  });

  const openEdit = (addr: ShippingAddress) => {
    setEditingId(addr.id);
    setFormError('');
    setForm({
      label: addr.label,
      street_line_1: addr.street_line_1,
      street_line_2: addr.street_line_2 || '',
      city: addr.city,
      state: addr.state,
      postal_code: addr.postal_code,
      country: addr.country,
      recipient_name: addr.recipient_name || '',
      phone: addr.phone || '',
      user_id: addr.user_id || '',
      is_office: addr.is_office,
    });
    setShowForm(true);
  };

  const openCreate = () => {
    setEditingId(null);
    setFormError('');
    setForm(emptyForm);
    setShowForm(true);
  };

  const openCreateEmployee = (userId = '') => {
    setEditingId(null);
    setFormError('');
    setForm({
      ...emptyForm,
      is_office: false,
      user_id: userId,
    });
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingId(null);
    setFormError('');
    setForm(emptyForm);
  };

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.addresses.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.addresses.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          {showForm ? (
            <button
              onClick={closeForm}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
            >
              {t('common.close')}
            </button>
          ) : (
            <>
              <button
                onClick={() => openCreateEmployee()}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
              >
                {t('page.addresses.new_employee')}
              </button>
              <button
                onClick={openCreate}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {t('page.addresses.new')}
              </button>
            </>
          )}
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        <select
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
          className="w-56 text-sm bg-card"
        >
          <option value="">{t('page.addresses.filter_all')}</option>
          <option value="office">{t('page.addresses.filter_office')}</option>
          <option value="employee">{t('page.addresses.filter_employee')}</option>
        </select>
      </div>

      {showForm && (
        <Card className="mb-4 overflow-hidden p-0">
          <div className="border-b border-border px-5 py-3.5">
            <h3 className="text-sm font-medium text-foreground">
              {editingId ? t('page.addresses.form_edit') : t('page.addresses.form_new')}
            </h3>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (editingId) updateAddress.mutate();
              else createAddress.mutate();
            }}
            className="space-y-4 p-5"
          >
            {formError && (
              <div className="rounded-md border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {formError}
              </div>
            )}

            {usersError && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <span>{t('page.addresses.error_users_load')}</span>
                <button
                  type="button"
                  onClick={() => { void refetchUsers(); }}
                  className="inline-flex items-center justify-center rounded-md border border-destructive/30 bg-background px-3 py-1 text-xs font-medium text-foreground hover:bg-accent"
                >
                  {t('common.retry')}
                </button>
              </div>
            )}

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.addresses.label')}</label>
                <input
                  value={form.label}
                  onChange={(e) => { setFormError(''); setForm({ ...form, label: e.target.value }); }}
                  required
                  className="w-full bg-card"
                />
              </div>
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.addresses.recipient')}</label>
                <input
                  value={form.recipient_name}
                  onChange={(e) => { setFormError(''); setForm({ ...form, recipient_name: e.target.value }); }}
                  className="w-full bg-card"
                />
              </div>
            </div>
            <div>
              <label className="block mb-1.5 text-muted-foreground">{t('page.addresses.street')}</label>
              <input
                value={form.street_line_1}
                onChange={(e) => { setFormError(''); setForm({ ...form, street_line_1: e.target.value }); }}
                required
                className="w-full bg-card"
              />
            </div>
            <input
              value={form.street_line_2}
              onChange={(e) => { setFormError(''); setForm({ ...form, street_line_2: e.target.value }); }}
              placeholder="Street line 2"
              className="w-full bg-card"
            />
            <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.addresses.city')}</label>
                <input
                  value={form.city}
                  onChange={(e) => { setFormError(''); setForm({ ...form, city: e.target.value }); }}
                  required
                  className="w-full bg-card"
                />
              </div>
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.addresses.state')}</label>
                <input
                  value={form.state}
                  onChange={(e) => { setFormError(''); setForm({ ...form, state: e.target.value }); }}
                  required
                  className="w-full bg-card"
                />
              </div>
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.addresses.postal_code')}</label>
                <input
                  value={form.postal_code}
                  onChange={(e) => { setFormError(''); setForm({ ...form, postal_code: e.target.value }); }}
                  required
                  className="w-full bg-card"
                />
              </div>
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.addresses.country')}</label>
                <input
                  value={form.country}
                  onChange={(e) => { setFormError(''); setForm({ ...form, country: e.target.value }); }}
                  className="w-full bg-card"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.addresses.phone')}</label>
                <input
                  value={form.phone}
                  onChange={(e) => { setFormError(''); setForm({ ...form, phone: e.target.value }); }}
                  className="w-full bg-card"
                />
              </div>
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.addresses.user')}</label>
                <select
                  value={form.user_id}
                  onChange={(e) => { setFormError(''); setForm({ ...form, user_id: e.target.value }); }}
                  className="w-full bg-card"
                  disabled={usersLoading}
                >
                  <option value="">
                    {usersLoading ? t('page.addresses.loading_users') : t('page.addresses.select_user')}
                  </option>
                  {(users ?? []).map((u) => (
                    <option key={u.id} value={u.id}>{u.email}{u.name ? ` (${u.name})` : ''}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 py-2">
                  <input
                    type="checkbox"
                    checked={form.is_office}
                    onChange={(e) => { setFormError(''); setForm({ ...form, is_office: e.target.checked }); }}
                    className="rounded"
                  />
                  <span className="text-sm text-foreground">{t('page.addresses.is_office')}</span>
                </label>
              </div>
            </div>
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={closeForm}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                disabled={createAddress.isPending || updateAddress.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {editingId ? t('common.save') : t('common.create')}
              </button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => { void refetch(); }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.addresses.empty')} />
        ) : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>{t('page.addresses.label')}</Th>
                  <Th>{t('page.addresses.recipient')}</Th>
                  <Th>{t('page.addresses.city')}</Th>
                  <Th>{t('page.addresses.country')}</Th>
                  <Th>{t('table.type')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th>{t('table.actions')}</Th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((addr) => (
                  <tr key={addr.id}>
                    <Td><span className="font-medium">{addr.label}</span></Td>
                    <Td>{addr.recipient_name || '—'}</Td>
                    <Td>{addr.city}, {addr.state} {addr.postal_code}</Td>
                    <Td>{addr.country}</Td>
                    <Td>
                      <Badge variant={addr.is_office ? 'info' : 'default'}>
                        {addr.is_office ? t('page.addresses.filter_office') : t('page.addresses.filter_employee')}
                      </Badge>
                    </Td>
                    <Td>
                      <Badge variant={addr.is_active ? 'success' : 'default'}>
                        {addr.is_active ? t('enum.active') : t('enum.deactivated')}
                      </Badge>
                    </Td>
                    <Td>
                      <div className="flex gap-1">
                        <button
                          onClick={() => openEdit(addr)}
                          className="rounded-md px-2 py-1 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
                        >
                          {t('common.edit')}
                        </button>
                        {addr.is_active && (
                          <button
                            onClick={() => setDeactivateId(addr.id)}
                            className="rounded-md px-2 py-1 text-sm text-destructive hover:bg-accent hover:text-accent-foreground transition-colors"
                          >
                            {t('common.delete')}
                          </button>
                        )}
                      </div>
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
        open={deactivateId !== null}
        title={t('page.addresses.deactivate_title')}
        description={t('page.addresses.deactivate_desc')}
        onConfirm={() => { if (deactivateId) deactivateAddress.mutate(deactivateId); }}
        onCancel={() => setDeactivateId(null)}
        tone="danger"
      />
    </div>
  );
}
