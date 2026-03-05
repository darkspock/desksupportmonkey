import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';

interface PlanMrr {
  plan: string;
  count: number;
  mrr_cents: number;
}

interface Revenue {
  mrr_cents: number;
  mrr_formatted: string;
  new_mrr_cents: number;
  churned_mrr_cents: number;
  net_new_mrr_cents: number;
  by_plan: PlanMrr[];
}

interface TrialPipeline {
  active: number;
  expiring_7d: number;
  expiring_30d: number;
  started_this_month: number;
}

interface CompanyHealth {
  total_active: number;
  grace_period: number;
  suspended: number;
  complimentary: number;
  failed_payments: number;
}

interface Growth {
  new_7d: number;
  new_30d: number;
  mom_growth_pct: number | null;
}

interface Milestone {
  label: string;
  description: string;
  target_cents: number;
  current_cents: number;
  pct: number;
  achieved: boolean;
}

interface UpcomingRenewal {
  company_id: string;
  company_name: string;
  plan: string;
  period_end: string;
}

interface DashboardData {
  revenue: Revenue;
  trials: TrialPipeline;
  health: CompanyHealth;
  growth: Growth;
  next_milestone: Milestone;
  upcoming_renewals_7d: UpcomingRenewal[];
  as_of: string;
}

function formatCents(cents: number): string {
  const amount = cents / 100;
  return `€${amount.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-bold text-foreground">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>}
    </div>
  );
}

function MiniStat({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={`text-sm font-medium ${color ?? 'text-foreground'}`}>{value}</span>
    </div>
  );
}

export default function FounderDashboardPage() {
  const { t } = useI18n();

  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ['founder-dashboard'],
    queryFn: async () => {
      const { data } = await api.get('/super-admin/dashboard');
      return data.data as DashboardData;
    },
    staleTime: 30_000,
  });

  if (isLoading || !data) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground">Loading...</div>
    );
  }

  const { revenue, trials, health, growth, next_milestone, upcoming_renewals_7d } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">{t('page.founder_dashboard.title')}</h1>
        <span className="text-xs text-muted-foreground">
          {new Date(data.as_of).toLocaleString()}
        </span>
      </div>

      {/* Revenue Section */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          {t('page.founder_dashboard.revenue')}
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="MRR" value={revenue.mrr_formatted} />
          <StatCard label={t('page.founder_dashboard.net_new_mrr')} value={formatCents(revenue.net_new_mrr_cents)} />
          <StatCard label={t('page.founder_dashboard.new_mrr')} value={formatCents(revenue.new_mrr_cents)} />
          <StatCard label={t('page.founder_dashboard.churned_mrr')} value={formatCents(revenue.churned_mrr_cents)} />
        </div>
        {revenue.by_plan.length > 0 && (
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xs font-medium text-muted-foreground mb-2">{t('page.founder_dashboard.mrr_by_plan')}</p>
            {revenue.by_plan.map((p) => (
              <div key={p.plan} className="flex items-center justify-between py-1 text-sm">
                <span className="capitalize text-foreground">{p.plan}</span>
                <span className="text-muted-foreground">
                  {p.count} × {formatCents(p.mrr_cents)}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Milestone */}
      <section className="rounded-lg border border-border bg-card p-4 space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-foreground">
            {t('page.founder_dashboard.next_milestone')}
          </h2>
          {next_milestone.achieved && (
            <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
              {t('page.founder_dashboard.achieved')}
            </span>
          )}
        </div>
        <p className="text-sm text-muted-foreground">{next_milestone.description}</p>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2.5 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${Math.min(next_milestone.pct, 100)}%` }}
            />
          </div>
          <span className="text-sm font-medium text-foreground">{next_milestone.pct}%</span>
        </div>
        <p className="text-xs text-muted-foreground">
          {formatCents(next_milestone.current_cents)} / {formatCents(next_milestone.target_cents)}
        </p>
      </section>

      {/* Trial Pipeline + Health */}
      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-lg border border-border bg-card p-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">
            {t('page.founder_dashboard.trial_pipeline')}
          </h2>
          <MiniStat label={t('page.founder_dashboard.trials_active')} value={trials.active} />
          <MiniStat label={t('page.founder_dashboard.trials_expiring_7d')} value={trials.expiring_7d} color={trials.expiring_7d > 0 ? 'text-yellow-600' : undefined} />
          <MiniStat label={t('page.founder_dashboard.trials_expiring_30d')} value={trials.expiring_30d} />
          <MiniStat label={t('page.founder_dashboard.trials_started_month')} value={trials.started_this_month} />
        </section>

        <section className="rounded-lg border border-border bg-card p-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">
            {t('page.founder_dashboard.company_health')}
          </h2>
          <MiniStat label={t('page.founder_dashboard.total_active')} value={health.total_active} />
          <MiniStat label={t('page.founder_dashboard.grace_period')} value={health.grace_period} color={health.grace_period > 0 ? 'text-yellow-600' : undefined} />
          <MiniStat label={t('page.founder_dashboard.suspended')} value={health.suspended} color={health.suspended > 0 ? 'text-red-600' : undefined} />
          <MiniStat label={t('page.founder_dashboard.complimentary')} value={health.complimentary} />
          <MiniStat label={t('page.founder_dashboard.failed_payments')} value={health.failed_payments} color={health.failed_payments > 0 ? 'text-red-600' : undefined} />
        </section>
      </div>

      {/* Growth */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          {t('page.founder_dashboard.growth')}
        </h2>
        <div className="grid grid-cols-3 gap-3">
          <StatCard label={t('page.founder_dashboard.new_7d')} value={growth.new_7d} />
          <StatCard label={t('page.founder_dashboard.new_30d')} value={growth.new_30d} />
          <StatCard
            label={t('page.founder_dashboard.mom_growth')}
            value={growth.mom_growth_pct != null ? `${growth.mom_growth_pct.toFixed(1)}%` : '—'}
          />
        </div>
      </section>

      {/* Upcoming Renewals */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          {t('page.founder_dashboard.upcoming_renewals')}
        </h2>
        {upcoming_renewals_7d.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('page.founder_dashboard.no_renewals')}</p>
        ) : (
          <div className="rounded-lg border border-border bg-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-left text-xs text-muted-foreground">
                  <th className="px-4 py-2 font-medium">{t('page.founder_dashboard.renewal_company')}</th>
                  <th className="px-4 py-2 font-medium">{t('page.founder_dashboard.renewal_plan')}</th>
                  <th className="px-4 py-2 font-medium">{t('page.founder_dashboard.renewal_date')}</th>
                </tr>
              </thead>
              <tbody>
                {upcoming_renewals_7d.map((r) => (
                  <tr key={r.company_id} className="border-b border-border/50">
                    <td className="px-4 py-2 font-medium text-foreground">{r.company_name}</td>
                    <td className="px-4 py-2 capitalize text-muted-foreground">{r.plan}</td>
                    <td className="px-4 py-2 text-muted-foreground">{new Date(r.period_end).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
