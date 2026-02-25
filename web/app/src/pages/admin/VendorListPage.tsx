import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Pencil } from 'lucide-react';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { Pagination } from '../../components/ui/Pagination';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useAuth } from '../../contexts/AuthContext';
import type { Vendor, PaginatedResponse } from '../../types';

type FormField = 'name' | 'contact_email' | 'phone' | 'address' | 'notes';

interface VendorFormValues {
  name: string;
  contact_email: string;
  phone: string;
  address: string;
  notes: string;
}

interface VendorFormErrors {
  name?: string;
  contact_email?: string;
}

const EMPTY_FORM: VendorFormValues = {
  name: '',
  contact_email: '',
  phone: '',
  address: '',
  notes: '',
};

function DeactivateIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="m4.9 4.9 14.2 14.2" />
    </svg>
  );
}

function ActivateIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <path d="m9 11 3 3L22 4" />
    </svg>
  );
}

export default function VendorListPage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin' || user?.role === 'procurement_manager';

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [showForm, setShowForm] = useState(false);
  const [editVendor, setEditVendor] = useState<Vendor | null>(null);
  const [formValues, setFormValues] = useState<VendorFormValues>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<VendorFormErrors>({});
  const [formTouched, setFormTouched] = useState<Partial<Record<FormField, boolean>>>({});
  const [formErrorMessage, setFormErrorMessage] = useState('');
  const [pendingStatusChange, setPendingStatusChange] = useState<Vendor | null>(null);
  const pageSize = 20;

  const isActiveParam = activeFilter === 'active' ? true : activeFilter === 'inactive' ? false : undefined;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['vendors', page, search, activeFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', String(pageSize));
      if (search) params.set('search', search);
      if (isActiveParam !== undefined) params.set('is_active', String(isActiveParam));
      const { data } = await api.get(`/vendors?${params}`);
      return data as PaginatedResponse<Vendor>;
    },
  });

  const vendors = data?.data ?? [];
  const total = data?.meta?.total ?? 0;

  const resetForm = () => {
    setFormValues(EMPTY_FORM);
    setFormErrors({});
    setFormTouched({});
    setFormErrorMessage('');
    setEditVendor(null);
    setShowForm(false);
  };

  const validateForm = (values: VendorFormValues): VendorFormErrors => {
    const errors: VendorFormErrors = {};
    if (!values.name.trim()) {
      errors.name = t('page.vendors.error_name_required');
    }
    if (values.contact_email.trim()) {
      const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.contact_email.trim());
      if (!isValidEmail) {
        errors.contact_email = t('page.vendors.error_email_invalid');
      }
    }
    return errors;
  };

  const touchField = (field: FormField) => {
    setFormTouched((prev) => ({ ...prev, [field]: true }));
    setFormErrors(validateForm(formValues));
  };

  const updateField = (field: FormField, value: string) => {
    const nextValues = { ...formValues, [field]: value };
    setFormValues(nextValues);
    if (formTouched[field]) {
      setFormErrors(validateForm(nextValues));
    }
  };

  const openCreate = () => {
    setEditVendor(null);
    setFormValues(EMPTY_FORM);
    setFormErrors({});
    setFormTouched({});
    setFormErrorMessage('');
    setShowForm(true);
  };

  const openEdit = (v: Vendor) => {
    setEditVendor(v);
    setFormValues({
      name: v.name,
      contact_email: v.contact_email || '',
      phone: v.phone || '',
      address: v.address || '',
      notes: v.notes || '',
    });
    setFormErrors({});
    setFormTouched({});
    setFormErrorMessage('');
    setShowForm(true);
  };

  const create = useMutation({
    mutationFn: async () => {
      await api.post('/vendors', {
        name: formValues.name.trim(),
        contact_email: formValues.contact_email.trim() || null,
        phone: formValues.phone.trim() || null,
        address: formValues.address.trim() || null,
        notes: formValues.notes.trim() || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
      resetForm();
      showToast({ title: t('page.vendors.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.vendors.error_generic');
      setFormErrorMessage(detail);
      showToast({ title: t('page.vendors.error_create'), description: detail, variant: 'error' });
    },
  });

  const update = useMutation({
    mutationFn: async () => {
      if (!editVendor) return;
      await api.put(`/vendors/${editVendor.id}`, {
        name: formValues.name.trim(),
        contact_email: formValues.contact_email.trim() || null,
        phone: formValues.phone.trim() || null,
        address: formValues.address.trim() || null,
        notes: formValues.notes.trim() || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
      resetForm();
      showToast({ title: t('page.vendors.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.vendors.error_generic');
      setFormErrorMessage(detail);
      showToast({ title: t('page.vendors.error_update'), description: detail, variant: 'error' });
    },
  });

  const toggleActive = useMutation({
    mutationFn: async (v: Vendor) => {
      const action = v.is_active ? 'deactivate' : 'activate';
      await api.post(`/vendors/${v.id}/${action}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
      showToast({ title: t('page.vendors.toast_status_changed'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.vendors.error_generic');
      showToast({ title: t('page.vendors.error_status'), description: detail, variant: 'error' });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const allTouched: Partial<Record<FormField, boolean>> = {
      name: true,
      contact_email: true,
      phone: true,
      address: true,
      notes: true,
    };
    setFormTouched(allTouched);
    const errors = validateForm(formValues);
    setFormErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }
    setFormErrorMessage('');
    if (editVendor) {
      update.mutate();
    } else {
      create.mutate();
    }
  };

  return (
    <div>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.vendors.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.vendors.subtitle')}</p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {t('page.vendors.create_button')}
        </button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center mb-4">
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
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder={t('page.vendors.search_placeholder')}
            className="w-full pl-9 bg-card"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <select
            value={activeFilter}
            onChange={(e) => { setActiveFilter(e.target.value); setPage(1); }}
            className="w-[150px] bg-card"
          >
            <option value="all">{t('page.vendors.filter_all')}</option>
            <option value="active">{t('page.vendors.filter_active')}</option>
            <option value="inactive">{t('page.vendors.filter_inactive')}</option>
          </select>
        </div>
      </div>

      <Card>
        {isLoading ? <Loading /> : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.vendors.error_load')}
            onRetry={() => { void refetch(); }}
          />
        ) : !vendors.length ? (
          <EmptyState message={t('page.vendors.empty')} />
        ) : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>{t('page.vendors.name')}</Th>
                  <Th>{t('page.vendors.email')}</Th>
                  <Th>{t('page.vendors.phone')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th>{t('page.vendors.created')}</Th>
                  <th className="px-4 py-2 text-right font-medium text-foreground">{t('table.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {vendors.map((v) => (
                  <tr key={v.id}>
                    <Td>{v.name}</Td>
                    <Td>{v.contact_email || '—'}</Td>
                    <Td>{v.phone || '—'}</Td>
                    <Td>
                      <Badge variant={v.is_active ? 'success' : 'danger'}>
                        {v.is_active ? t('page.vendors.active') : t('page.vendors.inactive')}
                      </Badge>
                    </Td>
                    <Td>{v.created_at ? formatDate(v.created_at) : '—'}</Td>
                    <td className="px-4 py-3 text-sm text-foreground">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => openEdit(v)}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-secondary"
                          aria-label={t('common.edit')}
                          title={t('common.edit')}
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        {isAdmin && (
                          <button
                            onClick={() => setPendingStatusChange(v)}
                            disabled={toggleActive.isPending}
                            className={`inline-flex h-8 w-8 items-center justify-center rounded-md border hover:bg-secondary disabled:opacity-50 ${
                              v.is_active
                                ? 'border-destructive/20 text-destructive'
                                : 'border-success/20 text-success'
                            }`}
                            aria-label={v.is_active ? t('page.vendors.deactivate') : t('page.vendors.activate')}
                            title={v.is_active ? t('page.vendors.deactivate') : t('page.vendors.activate')}
                          >
                            {v.is_active ? <DeactivateIcon /> : <ActivateIcon />}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={page} pageSize={pageSize} total={total} onChange={setPage} />
          </>
        )}
      </Card>

      {showForm && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (!create.isPending && !update.isPending) resetForm();
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-2xl rounded-xl border border-border bg-card p-6 shadow-lg">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-foreground">
                  {editVendor ? t('page.vendors.edit_title') : t('page.vendors.create_title')}
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {editVendor ? t('page.vendors.edit_subtitle') : t('page.vendors.create_subtitle')}
                </p>
              </div>
              <button
                type="button"
                onClick={resetForm}
                disabled={create.isPending || update.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
              >
                {t('common.close')}
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {formErrorMessage && (
                <div className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {formErrorMessage}
                </div>
              )}

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('page.vendors.name')}</label>
                  <input
                    value={formValues.name}
                    onChange={(e) => updateField('name', e.target.value)}
                    onBlur={() => touchField('name')}
                    maxLength={200}
                    autoFocus
                    className={`w-full bg-card ${
                      formErrors.name ? 'border-destructive/40' : ''
                    }`}
                  />
                  {formErrors.name && formTouched.name && (
                    <p className="mt-1 text-xs text-destructive">{formErrors.name}</p>
                  )}
                </div>

                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('page.vendors.email')}</label>
                  <input
                    type="email"
                    value={formValues.contact_email}
                    onChange={(e) => updateField('contact_email', e.target.value)}
                    onBlur={() => touchField('contact_email')}
                    maxLength={254}
                    className={`w-full bg-card ${
                      formErrors.contact_email ? 'border-destructive/40' : ''
                    }`}
                  />
                  {formErrors.contact_email && formTouched.contact_email && (
                    <p className="mt-1 text-xs text-destructive">{formErrors.contact_email}</p>
                  )}
                </div>

                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('page.vendors.phone')}</label>
                  <input
                    value={formValues.phone}
                    onChange={(e) => updateField('phone', e.target.value)}
                    onBlur={() => touchField('phone')}
                    maxLength={50}
                    className="w-full bg-card"
                  />
                </div>

                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('page.vendors.address')}</label>
                  <input
                    value={formValues.address}
                    onChange={(e) => updateField('address', e.target.value)}
                    onBlur={() => touchField('address')}
                    className="w-full bg-card"
                  />
                </div>
              </div>

              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('page.vendors.notes')}</label>
                <textarea
                  value={formValues.notes}
                  onChange={(e) => updateField('notes', e.target.value)}
                  onBlur={() => touchField('notes')}
                  rows={3}
                  className="w-full bg-card"
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={resetForm}
                  disabled={create.isPending || update.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={create.isPending || update.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {create.isPending || update.isPending
                    ? t('common.working')
                    : editVendor
                      ? t('common.save')
                      : t('common.create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={Boolean(pendingStatusChange)}
        title={pendingStatusChange?.is_active ? t('page.vendors.confirm_deactivate_title') : t('page.vendors.confirm_activate_title')}
        description={
          pendingStatusChange
            ? t('page.vendors.confirm_status_desc', {
              name: pendingStatusChange.name,
              action: pendingStatusChange.is_active ? t('page.vendors.deactivate').toLowerCase() : t('page.vendors.activate').toLowerCase(),
            })
            : ''
        }
        confirmLabel={pendingStatusChange?.is_active ? t('page.vendors.deactivate') : t('page.vendors.activate')}
        tone={pendingStatusChange?.is_active ? 'danger' : 'default'}
        busy={toggleActive.isPending}
        onCancel={() => setPendingStatusChange(null)}
        onConfirm={() => {
          if (!pendingStatusChange) return;
          toggleActive.mutate(pendingStatusChange, { onSettled: () => setPendingStatusChange(null) });
        }}
      />
    </div>
  );
}
