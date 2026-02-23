import { useState, useEffect } from 'react';
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
  trial_days_remaining: number | null;
  trial_ends_at: string | null;
}

interface Invoice {
  invoice_id: string;
  date: string;
  period_start: string;
  period_end: string;
  amount_cents: number;
  currency: string;
  status: string;
  invoice_url: string | null;
  pdf_url: string | null;
}

const PLAN_OPTIONS = ['free', 'premium', 'enterprise', 'open_source'];

const planLabel: Record<string, string> = {
  free: 'Free',
  premium: 'Premium',
  enterprise: 'Enterprise',
  open_source: 'Open Source',
};

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  grace_period: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  suspended: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  over_limit: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
};

const invoiceStatusColors: Record<string, string> = {
  paid: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  open: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  draft: 'bg-muted text-muted-foreground',
  void: 'bg-muted text-muted-foreground',
  uncollectible: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
};

const planColors: Record<string, string> = {
  free: 'bg-muted text-muted-foreground',
  premium: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  enterprise: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  open_source: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
};

type Tab = 'billing' | 'invoices';

/* Shared styles */
const btnPrimary = 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50 transition-all';
const btnOutline = 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground disabled:opacity-50 transition-all';
const btnDestructiveOutline = 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border border-destructive text-destructive shadow-xs hover:bg-destructive hover:text-destructive-foreground disabled:opacity-50 transition-all';
const btnPurple = 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-purple-600 text-white shadow-xs hover:bg-purple-700 disabled:opacity-50 transition-all';

interface Props {
  companyId: string;
  companyName: string;
  onClose: () => void;
}

function formatCurrency(cents: number, currency: string): string {
  const amount = cents / 100;
  const sym = currency === 'eur' ? '€' : currency === 'usd' ? '$' : currency.toUpperCase() + ' ';
  return `${sym}${amount.toFixed(2)}`;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}/${mm}/${dd}`;
}

export function CompanyBillingModal({ companyId, companyName, onClose }: Props) {
  const { t } = useI18n();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [overridePlan, setOverridePlan] = useState('');
  const [grantPlan, setGrantPlan] = useState('enterprise');
  const [activeTab, setActiveTab] = useState<Tab>('billing');

  const { data, isLoading } = useQuery<BillingData>({
    queryKey: ['company-billing', companyId],
    queryFn: async () => {
      const { data } = await api.get(`/companies/${companyId}/billing`);
      return data as BillingData;
    },
  });

  // Initialize overridePlan to current plan once loaded
  useEffect(() => {
    if (data && !overridePlan) {
      setOverridePlan(data.plan);
    }
  }, [data, overridePlan]);

  const { data: invoices, isLoading: invoicesLoading } = useQuery<Invoice[]>({
    queryKey: ['company-invoices', companyId],
    queryFn: async () => {
      const { data } = await api.get(`/companies/${companyId}/invoices`);
      return data as Invoice[];
    },
    enabled: activeTab === 'invoices',
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

  const planChanged = data && overridePlan !== data.plan;

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
      <button type="button" className="absolute inset-0 bg-black/40" onClick={onClose} aria-label={t('common.close')} />
      <div className="relative z-[91] w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">
            {t('page.companies.billing_modal_title')} — {companyName}
          </h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground" aria-label={t('common.close')}>
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('billing')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'billing'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {t('page.companies.billing_tab')}
          </button>
          <button
            onClick={() => setActiveTab('invoices')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'invoices'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {t('page.companies.invoices_tab')}
          </button>
        </div>

        {/* ── Billing Tab ──────────────────────────────────────────── */}
        {activeTab === 'billing' && (
          <>
            {isLoading || !data ? (
              <div className="py-6 text-center text-sm text-muted-foreground">Loading...</div>
            ) : (
              <>
                {/* ── Change Plan (prominent, first section) ──────── */}
                <div className="rounded-lg border-2 border-primary/20 bg-primary/5 p-4 space-y-3">
                  <p className="text-sm font-semibold text-foreground">{t('page.companies.override_plan')}</p>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-muted-foreground">{t('page.companies.billing.current')}:</span>
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${planColors[data.plan] ?? planColors.free}`}>
                      {planLabel[data.plan] ?? data.plan}
                    </span>
                  </div>
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
                      disabled={overrideMutation.isPending || !planChanged}
                      className={btnPrimary}
                    >
                      {t('page.companies.billing_apply')}
                    </button>
                  </div>
                </div>

                {/* Trial Info */}
                {data.trial_days_remaining != null && (
                  <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm dark:border-blue-800 dark:bg-blue-900/20">
                    <p className="font-medium text-blue-800 dark:text-blue-300">
                      {t('page.companies.billing.in_trial')}
                    </p>
                    <p className="text-blue-700 dark:text-blue-400">
                      {data.trial_days_remaining} {t('page.companies.billing.days_remaining')}
                      {data.trial_ends_at && ` · ${t('page.companies.billing.expires')} ${formatDate(data.trial_ends_at)}`}
                    </p>
                  </div>
                )}

                {/* Current Billing Status */}
                <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">{t('page.companies.billing_status_column')}</span>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[data.billing_status] ?? 'bg-muted text-foreground'}`}>
                      {data.billing_status}
                    </span>
                  </div>
                  {data.complimentary && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Complimentary</span>
                      <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300">Yes</span>
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
                      <span className="text-xs">{formatDate(data.current_period_end)}</span>
                    </div>
                  )}
                  {data.pending_downgrade_plan && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Pending Downgrade</span>
                      <span className="text-xs">{planLabel[data.pending_downgrade_plan] ?? data.pending_downgrade_plan}</span>
                    </div>
                  )}
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
                        className={btnPurple}
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
                      className={btnDestructiveOutline}
                    >
                      {t('page.companies.revoke_complimentary')}
                    </button>
                  </div>
                )}
              </>
            )}
          </>
        )}

        {/* ── Invoices Tab ─────────────────────────────────────────── */}
        {activeTab === 'invoices' && (
          <>
            {invoicesLoading ? (
              <div className="py-6 text-center text-sm text-muted-foreground">Loading...</div>
            ) : !invoices || invoices.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">
                {t('page.companies.invoices_empty')}
              </div>
            ) : (
              <div className="max-h-80 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-card">
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="pb-2 font-medium">{t('page.companies.invoices_date')}</th>
                      <th className="pb-2 font-medium">{t('page.companies.invoices_amount')}</th>
                      <th className="pb-2 font-medium">{t('page.companies.invoices_status')}</th>
                      <th className="pb-2 font-medium text-right">{t('page.companies.invoices_actions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoices.map((inv) => (
                      <tr key={inv.invoice_id} className="border-b border-border/50">
                        <td className="py-2">
                          <div>{formatDate(inv.date)}</div>
                          <div className="text-xs text-muted-foreground">
                            {formatDate(inv.period_start)} – {formatDate(inv.period_end)}
                          </div>
                        </td>
                        <td className="py-2 font-medium">
                          {formatCurrency(inv.amount_cents, inv.currency)}
                        </td>
                        <td className="py-2">
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${invoiceStatusColors[inv.status] ?? 'bg-muted text-foreground'}`}>
                            {inv.status}
                          </span>
                        </td>
                        <td className="py-2 text-right space-x-2">
                          {inv.invoice_url && (
                            <a
                              href={inv.invoice_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary hover:underline"
                            >
                              {t('page.companies.invoices_view')}
                            </a>
                          )}
                          {inv.pdf_url && (
                            <a
                              href={inv.pdf_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary hover:underline"
                            >
                              PDF
                            </a>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
