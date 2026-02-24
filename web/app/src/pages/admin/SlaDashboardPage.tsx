import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';

interface ComplianceByGroup {
  group: string;
  total: number;
  met: number;
  breached: number;
  compliance_pct: number;
}

interface BreachTrendPoint {
  period: string;
  count: number;
}

interface DashboardData {
  total_resolved: number;
  met: number;
  breached: number;
  compliance_pct: number;
  by_priority: ComplianceByGroup[];
  by_type: ComplianceByGroup[];
  breach_trend: BreachTrendPoint[];
}

function defaultRange() {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 30);
  return {
    from: from.toISOString().slice(0, 10),
    to: to.toISOString().slice(0, 10),
  };
}

export default function SlaDashboardPage() {
  const { t } = useI18n();
  const defaults = defaultRange();
  const [fromDate, setFromDate] = useState(defaults.from);
  const [toDate, setToDate] = useState(defaults.to);
  const [bucket, setBucket] = useState<'day' | 'week' | 'month'>('week');

  const { data: dashboard, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['sla-dashboard', fromDate, toDate, bucket],
    queryFn: async () => {
      const { data } = await api.get('/sla/dashboard', {
        params: {
          from_date: `${fromDate}T00:00:00Z`,
          to_date: `${toDate}T23:59:59Z`,
          bucket,
        },
      });
      return data.data as DashboardData;
    },
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error).message} onRetry={refetch} />;
  if (!dashboard) return null;

  const maxTrend = Math.max(...dashboard.breach_trend.map((p) => p.count), 1);

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {t('page.sla_dashboard.title')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('page.sla_dashboard.subtitle')}
          </p>
        </div>
        <Link to="/sla/policies" className="text-sm text-primary hover:underline">
          {t('page.sla_dashboard.manage_policies')}
        </Link>
      </div>

      {/* Date Range Filters */}
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">
            {t('page.sla_dashboard.from_date')}
          </label>
          <input
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">
            {t('page.sla_dashboard.to_date')}
          </label>
          <input
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">
            {t('page.sla_dashboard.bucket')}
          </label>
          <select
            value={bucket}
            onChange={(e) => setBucket(e.target.value as 'day' | 'week' | 'month')}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground"
          >
            <option value="day">{t('page.sla_dashboard.bucket_day')}</option>
            <option value="week">{t('page.sla_dashboard.bucket_week')}</option>
            <option value="month">{t('page.sla_dashboard.bucket_month')}</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label={t('page.sla_dashboard.compliance_rate')}
          value={`${dashboard.compliance_pct}%`}
          variant={dashboard.compliance_pct >= 90 ? 'success' : dashboard.compliance_pct >= 70 ? 'warning' : 'danger'}
        />
        <StatCard label={t('page.sla_dashboard.total_resolved')} value={dashboard.total_resolved} />
        <StatCard label={t('page.sla_dashboard.sla_met')} value={dashboard.met} variant="success" />
        <StatCard label={t('page.sla_dashboard.sla_breached')} value={dashboard.breached} variant="danger" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* By Priority */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">
            {t('page.sla_dashboard.by_priority')}
          </h3>
          {dashboard.by_priority.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t('page.sla_dashboard.no_data')}</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-muted-foreground border-b border-border">
                  <th className="text-left pb-2 font-medium">{t('page.sla.priority')}</th>
                  <th className="text-right pb-2 font-medium">{t('page.sla_dashboard.total')}</th>
                  <th className="text-right pb-2 font-medium">{t('page.sla_dashboard.met')}</th>
                  <th className="text-right pb-2 font-medium">{t('page.sla_dashboard.breached')}</th>
                  <th className="text-right pb-2 font-medium">%</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.by_priority.map((row) => (
                  <tr key={row.group} className="border-b border-border/50">
                    <td className="py-2 capitalize">{row.group}</td>
                    <td className="py-2 text-right">{row.total}</td>
                    <td className="py-2 text-right">
                      <Badge variant="success">{row.met}</Badge>
                    </td>
                    <td className="py-2 text-right">
                      {row.breached > 0 ? (
                        <Badge variant="danger">{row.breached}</Badge>
                      ) : (
                        <Badge variant="default">0</Badge>
                      )}
                    </td>
                    <td className="py-2 text-right font-medium">{row.compliance_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* By Type */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">
            {t('page.sla_dashboard.by_type')}
          </h3>
          {dashboard.by_type.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t('page.sla_dashboard.no_data')}</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-muted-foreground border-b border-border">
                  <th className="text-left pb-2 font-medium">{t('page.sla_dashboard.type')}</th>
                  <th className="text-right pb-2 font-medium">{t('page.sla_dashboard.total')}</th>
                  <th className="text-right pb-2 font-medium">{t('page.sla_dashboard.met')}</th>
                  <th className="text-right pb-2 font-medium">{t('page.sla_dashboard.breached')}</th>
                  <th className="text-right pb-2 font-medium">%</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.by_type.map((row) => (
                  <tr key={row.group} className="border-b border-border/50">
                    <td className="py-2 capitalize">{row.group.replace(/_/g, ' ')}</td>
                    <td className="py-2 text-right">{row.total}</td>
                    <td className="py-2 text-right">
                      <Badge variant="success">{row.met}</Badge>
                    </td>
                    <td className="py-2 text-right">
                      {row.breached > 0 ? (
                        <Badge variant="danger">{row.breached}</Badge>
                      ) : (
                        <Badge variant="default">0</Badge>
                      )}
                    </td>
                    <td className="py-2 text-right font-medium">{row.compliance_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Breach Trend */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">
          {t('page.sla_dashboard.breach_trend')}
        </h3>
        {dashboard.breach_trend.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('page.sla_dashboard.no_data')}</p>
        ) : (
          <div className="flex items-end gap-1 h-32">
            {dashboard.breach_trend.map((point) => (
              <div key={point.period} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-xs font-medium text-foreground">
                  {point.count > 0 ? point.count : ''}
                </span>
                <div
                  className={`w-full rounded-t ${
                    point.count > 0
                      ? 'bg-red-500/70 dark:bg-red-400/60'
                      : 'bg-muted/30'
                  }`}
                  style={{ height: `${Math.max((point.count / maxTrend) * 100, 4)}%` }}
                />
                <span className="text-[10px] text-muted-foreground truncate w-full text-center">
                  {point.period.slice(5)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  variant,
}: {
  label: string;
  value: number | string;
  variant?: 'warning' | 'success' | 'info' | 'danger';
}) {
  const colors: Record<string, string> = {
    warning: 'text-yellow-600 dark:text-yellow-400',
    success: 'text-green-600 dark:text-green-400',
    info: 'text-blue-600 dark:text-blue-400',
    danger: 'text-red-600 dark:text-red-400',
  };

  return (
    <div className="rounded-lg border border-border bg-card px-4 py-3">
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className={`mt-1 text-2xl font-semibold ${variant ? colors[variant] : 'text-foreground'}`}>
        {value}
      </dd>
    </div>
  );
}
