import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';

interface BillingOverview {
  plan: string;
  billing_status: string;
  complimentary: boolean;
  user_count: number;
  user_limit: number | null;
  asset_count: number;
  asset_limit: number | null;
  grace_days_remaining: number | null;
  current_period_end: string | null;
  pending_downgrade_plan: string | null;
  trial_days_remaining: number | null;
}

const PLAN_VARIANT: Record<string, string> = {
  free: 'bg-muted text-muted-foreground',
  starter: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300',
  premium: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  enterprise: 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300',
  open_source: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
};

const STATUS_VARIANT: Record<string, string> = {
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  grace_period: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
  suspended: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  over_limit: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
};

const PLAN_ORDER = ['free', 'starter', 'premium', 'enterprise'];

interface PlanOption {
  key: string;
  priceLabel: string;
  features: string[];
}

function PillBadge({ label, className }: { label: string; className: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${className}`}>
      {label}
    </span>
  );
}

function UsageBar({ label, used, limit }: { label: string; used: number; limit: number | null }) {
  const { t } = useI18n();
  const pct = limit === null ? 0 : Math.min(100, Math.round((used / limit) * 100));
  const barColor = pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-primary';

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-foreground">{label}</span>
        <span className="text-muted-foreground">
          {limit === null
            ? `${used} / ${t('page.billing.unlimited')}`
            : t('page.billing.usage_of', { used: String(used), limit: String(limit) })}
        </span>
      </div>
      {limit !== null && (
        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
          <div
            className={`h-2 rounded-full transition-all ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  );
}

function PlanPickerModal({
  currentPlan,
  onSelect,
  onClose,
  isPending,
}: {
  currentPlan: string;
  onSelect: (plan: string) => void;
  onClose: () => void;
  isPending: boolean;
}) {
  const { t } = useI18n();
  const [selected, setSelected] = useState<string | null>(null);
  const currentIdx = PLAN_ORDER.indexOf(currentPlan);

  const plans: PlanOption[] = [
    {
      key: 'starter',
      priceLabel: t('page.billing.plan_price.starter'),
      features: [
        t('page.billing.plan_feat.starter_1'),
        t('page.billing.plan_feat.starter_2'),
        t('page.billing.plan_feat.starter_3'),
      ],
    },
    {
      key: 'premium',
      priceLabel: t('page.billing.plan_price.premium'),
      features: [
        t('page.billing.plan_feat.premium_1'),
        t('page.billing.plan_feat.premium_2'),
        t('page.billing.plan_feat.premium_3'),
      ],
    },
    {
      key: 'enterprise',
      priceLabel: t('page.billing.plan_price.enterprise'),
      features: [
        t('page.billing.plan_feat.enterprise_1'),
        t('page.billing.plan_feat.enterprise_2'),
        t('page.billing.plan_feat.enterprise_3'),
      ],
    },
  ];

  const upgradePlans = plans.filter(p => PLAN_ORDER.indexOf(p.key) > currentIdx);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="mx-4 w-full max-w-2xl rounded-xl bg-background p-6 shadow-xl"
        onClick={e => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold text-foreground">{t('page.billing.pick_plan_title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.billing.pick_plan_subtitle')}</p>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {upgradePlans.map(plan => {
            const isSelected = selected === plan.key;
            return (
              <button
                key={plan.key}
                type="button"
                onClick={() => setSelected(plan.key)}
                className={`rounded-lg border-2 p-4 text-left transition-all ${
                  isSelected
                    ? 'border-primary bg-primary/5 ring-1 ring-primary'
                    : 'border-border hover:border-primary/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-foreground">
                    {t(`page.billing.plan.${plan.key}`)}
                  </span>
                  <PillBadge label={plan.priceLabel} className={PLAN_VARIANT[plan.key] ?? ''} />
                </div>
                <ul className="mt-3 space-y-1.5">
                  {plan.features.map((feat, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-xs text-muted-foreground">
                      <span className="mt-0.5 text-primary">&#10003;</span>
                      {feat}
                    </li>
                  ))}
                </ul>
              </button>
            );
          })}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-all"
          >
            {t('common.cancel')}
          </button>
          <button
            type="button"
            disabled={!selected || isPending}
            onClick={() => selected && onSelect(selected)}
            className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium shadow-xs bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all"
          >
            {isPending ? t('common.working') : t('page.billing.confirm_upgrade')}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BillingPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [showPicker, setShowPicker] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery<BillingOverview>({
    queryKey: ['billing-overview'],
    queryFn: async () => {
      const { data } = await api.get('/billing/');
      return data as BillingOverview;
    },
  });

  const checkoutMutation = useMutation({
    mutationFn: async (targetPlan: string) => {
      const { data } = await api.post('/billing/checkout', { target_plan: targetPlan });
      return data as { checkout_url: string };
    },
    onSuccess: ({ checkout_url }) => {
      window.location.href = checkout_url;
    },
    onError: () => {
      showToast({ title: t('page.billing.error_checkout'), variant: 'error' });
    },
  });

  const portalMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/billing/portal');
      return data as { portal_url: string };
    },
    onSuccess: ({ portal_url }) => {
      window.location.href = portal_url;
    },
    onError: () => {
      showToast({ title: t('page.billing.error_portal'), variant: 'error' });
    },
  });

  if (isLoading) return <Loading />;
  if (isError || !data) return <ErrorState onRetry={() => refetch()} />;

  const planLabel = t(`page.billing.plan.${data.plan}`) || data.plan;
  const statusLabel = t(`page.billing.status.${data.billing_status}`) || data.billing_status;
  const isGrace = data.billing_status === 'grace_period';
  const isSuspended = data.billing_status === 'suspended';
  const inTrial = data.trial_days_remaining !== null && data.trial_days_remaining > 0;
  const showStripeButtons = !data.complimentary && data.plan !== 'open_source';
  const isPlanUpgradable = data.plan !== 'enterprise' && data.plan !== 'open_source';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-foreground">{t('page.billing.title')}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.billing.subtitle')}</p>
      </div>

      {/* Trial banner */}
      {inTrial && (
        <div className="rounded-lg border border-blue-300 bg-blue-50 p-4 text-sm text-blue-800 dark:border-blue-700 dark:bg-blue-900/20 dark:text-blue-300">
          {t('page.billing.trial_banner', { days: String(data.trial_days_remaining) })}
        </div>
      )}

      {/* Grace period warning */}
      {isGrace && (
        <div className="rounded-lg border border-yellow-300 bg-yellow-50 p-4 text-sm text-yellow-800 dark:border-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-300">
          {data.grace_days_remaining !== null && data.grace_days_remaining > 0
            ? t('page.billing.grace_warning', { days: String(data.grace_days_remaining) })
            : t('page.billing.grace_warning_zero')}
        </div>
      )}

      {/* Suspended warning */}
      {isSuspended && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300">
          {t('page.billing.suspended_warning')}
        </div>
      )}

      {/* Plan overview */}
      <Card>
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">{t('page.billing.plan')}:</span>
              <PillBadge label={planLabel} className={PLAN_VARIANT[data.plan] ?? PLAN_VARIANT.free} />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">{t('page.billing.status')}:</span>
              <PillBadge label={statusLabel} className={STATUS_VARIANT[data.billing_status] ?? STATUS_VARIANT.active} />
            </div>
            {data.complimentary && (
              <PillBadge
                label={t('page.billing.complimentary')}
                className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
              />
            )}
            {inTrial && (
              <PillBadge
                label={t('page.billing.trial_badge', { days: String(data.trial_days_remaining) })}
                className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
              />
            )}
          </div>

          {/* Usage bars */}
          <div className="space-y-4 pt-2 border-t border-border">
            <UsageBar
              label={t('page.billing.users')}
              used={data.user_count}
              limit={data.user_limit}
            />
            <UsageBar
              label={t('page.billing.assets')}
              used={data.asset_count}
              limit={data.asset_limit}
            />
          </div>

          {/* Action buttons */}
          {showStripeButtons && (
            <div className="flex flex-wrap gap-3 pt-2 border-t border-border">
              {isPlanUpgradable && (
                <button
                  type="button"
                  onClick={() => setShowPicker(true)}
                  className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium shadow-xs transition-all disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  {t('page.billing.upgrade')}
                </button>
              )}
              <button
                type="button"
                onClick={() => portalMutation.mutate()}
                disabled={portalMutation.isPending}
                className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium shadow-xs transition-all disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground"
              >
                {portalMutation.isPending ? t('common.working') : t('page.billing.manage')}
              </button>
            </div>
          )}
        </div>
      </Card>

      {/* Current period info */}
      {data.current_period_end && (
        <p className="text-xs text-muted-foreground">
          {t('page.billing.period_ends', { date: new Date(data.current_period_end).toLocaleDateString() })}
        </p>
      )}

      {/* Pending downgrade */}
      {data.pending_downgrade_plan && (
        <p className="text-xs text-muted-foreground">
          {t('page.billing.pending_downgrade', {
            plan: t(`page.billing.plan.${data.pending_downgrade_plan}`) || data.pending_downgrade_plan,
          })}
        </p>
      )}

      {/* Back button for navigation */}
      <div>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          {t('common.back')}
        </button>
      </div>

      {/* Plan picker modal */}
      {showPicker && (
        <PlanPickerModal
          currentPlan={data.plan}
          onSelect={(plan) => checkoutMutation.mutate(plan)}
          onClose={() => setShowPicker(false)}
          isPending={checkoutMutation.isPending}
        />
      )}
    </div>
  );
}
