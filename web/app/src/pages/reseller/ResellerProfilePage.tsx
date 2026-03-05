import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useResellerAuth } from '../../contexts/ResellerAuthContext';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';
import api from '../../lib/api';

export default function ResellerProfilePage() {
  const { reseller, token, refreshReseller } = useResellerAuth();
  const { t } = useI18n();
  const { showToast } = useToast();

  const [companyName, setCompanyName] = useState(reseller?.company_name ?? '');
  const [taxId, setTaxId] = useState(reseller?.tax_id ?? '');
  const [editing, setEditing] = useState(false);

  const updateMutation = useMutation({
    mutationFn: async (payload: { company_name: string | null; tax_id: string | null }) => {
      await api.put('/reseller/profile', payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
    },
    onSuccess: async () => {
      await refreshReseller();
      setEditing(false);
      showToast({ title: t('reseller.profile.updated') });
    },
    onError: (error: unknown) => {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast({
        title: t('common.error'),
        description: detail ?? t('reseller.profile.update_error'),
        variant: 'error',
      });
    },
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate({
      company_name: companyName || null,
      tax_id: taxId || null,
    });
  };

  const handleCancel = () => {
    setCompanyName(reseller?.company_name ?? '');
    setTaxId(reseller?.tax_id ?? '');
    setEditing(false);
  };

  if (!reseller) return null;

  const isSuspended = reseller.status === 'suspended';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">{t('reseller.profile.title')}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t('reseller.profile.subtitle')}</p>
      </div>

      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-6 py-4">
          <h2 className="text-sm font-semibold text-foreground">{t('reseller.profile.account_info')}</h2>
        </div>
        <div className="grid gap-4 px-6 py-4 sm:grid-cols-2">
          <div>
            <p className="text-xs text-muted-foreground">{t('reseller.profile.email')}</p>
            <p className="mt-0.5 text-sm text-foreground">{reseller.email}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{t('reseller.profile.name')}</p>
            <p className="mt-0.5 text-sm text-foreground">{reseller.name}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{t('reseller.profile.commission')}</p>
            <p className="mt-0.5 text-sm text-foreground">{reseller.commission_pct}%</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{t('reseller.profile.min_payout')}</p>
            <p className="mt-0.5 text-sm text-foreground">${(reseller.min_payout_cents / 100).toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{t('reseller.profile.referral_code')}</p>
            <p className="mt-0.5 text-sm font-mono text-foreground">{reseller.referral_code}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{t('common.status')}</p>
            <p className="mt-0.5 text-sm capitalize text-foreground">{reseller.status}</p>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-sm font-semibold text-foreground">{t('reseller.profile.company_info')}</h2>
          {!editing && !isSuspended && (
            <button
              onClick={() => setEditing(true)}
              className="text-sm font-medium text-primary hover:underline"
            >
              {t('common.edit')}
            </button>
          )}
        </div>
        {editing ? (
          <form onSubmit={handleSave} className="px-6 py-4 space-y-4">
            <div>
              <label htmlFor="company_name" className="block mb-1.5 text-sm text-muted-foreground">
                {t('reseller.profile.company_name')}
              </label>
              <input
                id="company_name"
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder={t('reseller.profile.company_name_placeholder')}
                className="w-full"
              />
            </div>
            <div>
              <label htmlFor="tax_id" className="block mb-1.5 text-sm text-muted-foreground">
                {t('reseller.profile.tax_id')}
              </label>
              <input
                id="tax_id"
                type="text"
                value={taxId}
                onChange={(e) => setTaxId(e.target.value)}
                placeholder={t('reseller.profile.tax_id_placeholder')}
                className="w-full"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={handleCancel}
                className="rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground hover:bg-secondary"
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {updateMutation.isPending ? t('common.saving') : t('common.save')}
              </button>
            </div>
          </form>
        ) : (
          <div className="grid gap-4 px-6 py-4 sm:grid-cols-2">
            <div>
              <p className="text-xs text-muted-foreground">{t('reseller.profile.company_name')}</p>
              <p className="mt-0.5 text-sm text-foreground">{reseller.company_name || t('common.na')}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{t('reseller.profile.tax_id')}</p>
              <p className="mt-0.5 text-sm text-foreground">{reseller.tax_id || t('common.na')}</p>
            </div>
          </div>
        )}
        {isSuspended && (
          <div className="border-t border-border px-6 py-3">
            <p className="text-xs text-yellow-700">{t('reseller.profile.suspended_notice')}</p>
          </div>
        )}
      </div>

      {/* Change Password */}
      <ChangePasswordSection token={token} />
    </div>
  );
}

function ChangePasswordSection({ token }: { token: string | null }) {
  const { t } = useI18n();
  const { showToast } = useToast();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const changeMutation = useMutation({
    mutationFn: async (payload: { current_password: string; new_password: string }) => {
      await api.post('/reseller/change-password', payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
    },
    onSuccess: () => {
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setError('');
      showToast({ title: t('reseller.profile.password_changed') });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? t('common.error'));
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (newPassword !== confirmPassword) {
      setError(t('auth.set_password.error_mismatch'));
      return;
    }
    if (newPassword.length < 8) {
      setError(t('reseller.register.password_min_length'));
      return;
    }
    changeMutation.mutate({
      current_password: currentPassword,
      new_password: newPassword,
    });
  };

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-6 py-4">
        <h2 className="text-sm font-semibold text-foreground">{t('reseller.profile.change_password')}</h2>
      </div>
      <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
        {error && (
          <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}
        <div>
          <label htmlFor="cp-current" className="block mb-1.5 text-sm text-muted-foreground">
            {t('reseller.profile.current_password')}
          </label>
          <input
            id="cp-current"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            className="w-full"
          />
        </div>
        <div>
          <label htmlFor="cp-new" className="block mb-1.5 text-sm text-muted-foreground">
            {t('reseller.profile.new_password')}
          </label>
          <input
            id="cp-new"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={8}
            className="w-full"
          />
        </div>
        <div>
          <label htmlFor="cp-confirm" className="block mb-1.5 text-sm text-muted-foreground">
            {t('reseller.profile.confirm_password')}
          </label>
          <input
            id="cp-confirm"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
            className="w-full"
          />
        </div>
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={changeMutation.isPending}
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {changeMutation.isPending ? t('common.saving') : t('reseller.profile.change_password')}
          </button>
        </div>
      </form>
    </div>
  );
}
