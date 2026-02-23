import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';

interface BillingData {
  company_id: string;
  company_name: string;
  plan: string;
  billing_status: string;
  complimentary: boolean;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  current_period_end: string | null;
  pending_downgrade_plan: string | null;
  grace_period_started_at: string | null;
}

const PLAN_OPTIONS = ['free', 'premium', 'enterprise', 'open_source'];

const planLabel: Record<string, string> = {
  free: 'Free',
  premium: 'Premium',
  enterprise: 'Enterprise',
  open_source: 'Open Source',
};

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  grace_period: 'bg-yellow-100 text-yellow-800',
  suspended: 'bg-red-100 text-red-800',
  over_limit: 'bg-orange-100 text-orange-800',
};

interface Props {
  companyId: string;
  companyName: string;
  onClose: () => void;
}

export function CompanyBillingModal({ companyId, companyName, onClose }: Props) {
  const { t } = useI18n();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [overridePlan, setOverridePlan] = useState('free');
  const [grantPlan, setGrantPlan] = useState('enterprise');

  const { data, isLoading } = useQuery<BillingData>({
    queryKey: ['company-billing', companyId],
    queryFn: async () => {
      const { data } = await api.get(`/companies/${companyId}/billing`);
      return data as BillingData;
    },
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['company-billing', companyId] });
    queryClient.invalidateQueries({ queryKey: ['companies'] });
  };

  const overrideMutation = useMutation({
    mutationFn: () => api.patch(`/companies/${companyId}/billing/plan`, { new_plan: overridePlan }),
    onSuccess: () => {
      invalidate();
      showToast({ title: t('page.companies.toast_plan_overridden'), variant: 'success' });
    },
    onError: () => showToast({ title: t('page.companies.error_billing'), variant: 'error' }),
  });

  const grantMutation = useMutation({
    mutationFn: () => api.post(`/companies/${companyId}/billing/complimentary`, { plan: grantPlan }),
    onSuccess: () => {
      invalidate();
      showToast({ title: t('page.companies.toast_complimentary_granted'), variant: 'success' });
    },
    onError: () => showToast({ title: t('page.companies.error_billing'), variant: 'error' }),
  });

  const revokeMutation = useMutation({
    mutationFn: () => api.delete(`/companies/${companyId}/billing/complimentary`),
    onSuccess: () => {
      invalidate();
      showToast({ title: t('page.companies.toast_complimentary_revoked'), variant: 'success' });
    },
    onError: () => showToast({ title: t('page.companies.error_billing'), variant: 'error' }),
  });

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-[91] w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">
            {t('page.companies.billing_modal_title')} — {companyName}
          </h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">✕</button>
        </div>

        {isLoading || !data ? (
          <div className="py-6 text-center text-sm text-muted-foreground">Loading...</div>
        ) : (
          <>
            {/* Current Status */}
            <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t('page.companies.plan_column')}</span>
                <span className="font-medium">{planLabel[data.plan] ?? data.plan}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t('page.companies.billing_status_column')}</span>
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[data.billing_status] ?? 'bg-muted text-foreground'}`}>
                  {data.billing_status}
                </span>
              </div>
              {data.complimentary && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Complimentary</span>
                  <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-800">Yes</span>
                </div>
              )}
              {data.stripe_customer_id && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Stripe Customer</span>
                  <span className="font-mono text-xs">{data.stripe_customer_id}</span>
                </div>
              )}
              {data.stripe_subscription_id && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Stripe Sub</span>
                  <span className="font-mono text-xs">{data.stripe_subscription_id}</span>
                </div>
              )}
              {data.current_period_end && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Period End</span>
                  <span className="text-xs">{new Date(data.current_period_end).toLocaleDateString()}</span>
                </div>
              )}
              {data.pending_downgrade_plan && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Pending Downgrade</span>
                  <span className="text-xs">{planLabel[data.pending_downgrade_plan] ?? data.pending_downgrade_plan}</span>
                </div>
              )}
            </div>

            {/* Override Plan */}
            <div className="space-y-2">
              <p className="text-sm font-medium text-foreground">{t('page.companies.override_plan')}</p>
              <div className="flex items-center gap-2">
                <select
                  value={overridePlan}
                  onChange={(e) => setOverridePlan(e.target.value)}
                  className="flex-1 text-sm rounded-md border border-input bg-background px-3 py-2"
                >
                  {PLAN_OPTIONS.map((p) => (
                    <option key={p} value={p}>{planLabel[p]}</option>
                  ))}
                </select>
                <button
                  onClick={() => overrideMutation.mutate()}
                  disabled={overrideMutation.isPending}
                  className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
                >
                  {t('page.companies.billing_apply')}
                </button>
              </div>
            </div>

            {/* Grant Complimentary */}
            {!data.complimentary && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-foreground">{t('page.companies.grant_complimentary')}</p>
                <div className="flex items-center gap-2">
                  <select
                    value={grantPlan}
                    onChange={(e) => setGrantPlan(e.target.value)}
                    className="flex-1 text-sm rounded-md border border-input bg-background px-3 py-2"
                  >
                    {PLAN_OPTIONS.map((p) => (
                      <option key={p} value={p}>{planLabel[p]}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => grantMutation.mutate()}
                    disabled={grantMutation.isPending}
                    className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium bg-purple-600 text-white shadow-xs hover:bg-purple-700 disabled:opacity-50"
                  >
                    {t('page.companies.billing_grant')}
                  </button>
                </div>
              </div>
            )}

            {/* Revoke Complimentary */}
            {data.complimentary && (
              <div className="pt-1">
                <button
                  onClick={() => revokeMutation.mutate()}
                  disabled={revokeMutation.isPending}
                  className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium border border-destructive text-destructive shadow-xs hover:bg-destructive hover:text-destructive-foreground disabled:opacity-50"
                >
                  {t('page.companies.revoke_complimentary')}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
