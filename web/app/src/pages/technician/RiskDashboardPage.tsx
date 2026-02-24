import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';

interface DashboardData {
  total_risks: number;
  open_risks: number;
  mitigated_risks: number;
  accepted_risks: number;
  by_level: Record<string, number>;
  by_category: Record<string, number>;
  heat_map: { likelihood: number; impact: number; count: number }[];
  overdue_reviews: number;
  recent_risks: {
    id: string;
    title: string;
    category: string;
    status: string;
    risk_level: string | null;
    created_at: string | null;
  }[];
}

const levelVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  low: 'success',
  medium: 'info',
  high: 'warning',
  critical: 'danger',
};

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger' | 'purple'> = {
  open: 'warning',
  under_review: 'info',
  mitigated: 'success',
  accepted: 'purple',
  closed: 'default',
};

const HEAT_COLORS: Record<string, string> = {
  low: 'bg-green-500/20 text-green-700 dark:text-green-400',
  medium: 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400',
  high: 'bg-orange-500/20 text-orange-700 dark:text-orange-400',
  critical: 'bg-red-500/20 text-red-700 dark:text-red-400',
};

// Same matrix as backend
function levelForCell(l: number, i: number): string {
  const matrix: Record<string, string> = {
    '1,1': 'low', '1,2': 'low', '1,3': 'low', '1,4': 'medium', '1,5': 'medium',
    '2,1': 'low', '2,2': 'low', '2,3': 'medium', '2,4': 'medium', '2,5': 'high',
    '3,1': 'low', '3,2': 'medium', '3,3': 'medium', '3,4': 'high', '3,5': 'high',
    '4,1': 'medium', '4,2': 'medium', '4,3': 'high', '4,4': 'high', '4,5': 'critical',
    '5,1': 'medium', '5,2': 'high', '5,3': 'high', '5,4': 'critical', '5,5': 'critical',
  };
  return matrix[`${l},${i}`] || 'low';
}

export default function RiskDashboardPage() {
  const { t } = useI18n();

  const { data: dashboard, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['risk-dashboard'],
    queryFn: async () => {
      const { data } = await api.get('/risks/dashboard');
      return data.data as DashboardData;
    },
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error).message} onRetry={refetch} />;
  if (!dashboard) return null;

  const heatLookup = new Map<string, number>();
  for (const cell of dashboard.heat_map) {
    heatLookup.set(`${cell.likelihood},${cell.impact}`, cell.count);
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {t('page.risk_dashboard.title')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('page.risk_dashboard.subtitle')}
          </p>
        </div>
        <Link
          to="/risks"
          className="text-sm text-primary hover:underline"
        >
          {t('page.risk_dashboard.view_all')}
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <StatCard label={t('page.risk_dashboard.total')} value={dashboard.total_risks} />
        <StatCard label={t('page.risk_dashboard.open')} value={dashboard.open_risks} variant="warning" />
        <StatCard label={t('page.risk_dashboard.mitigated')} value={dashboard.mitigated_risks} variant="success" />
        <StatCard label={t('page.risk_dashboard.accepted')} value={dashboard.accepted_risks} variant="info" />
        <StatCard label={t('page.risk_dashboard.overdue')} value={dashboard.overdue_reviews} variant="danger" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* By Level */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">
            {t('page.risk_dashboard.by_level')}
          </h3>
          <div className="space-y-2">
            {['critical', 'high', 'medium', 'low'].map((level) => (
              <div key={level} className="flex items-center justify-between">
                <Badge variant={levelVariant[level] || 'default'}>
                  {t(`risk.level.${level}`)}
                </Badge>
                <span className="text-sm font-medium text-foreground">
                  {dashboard.by_level[level] || 0}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* By Category */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">
            {t('page.risk_dashboard.by_category')}
          </h3>
          <div className="space-y-2">
            {['cyber', 'operational', 'compliance', 'third_party'].map((cat) => (
              <div key={cat} className="flex items-center justify-between">
                <span className="text-sm text-foreground capitalize">
                  {t(`risk.category.${cat}`)}
                </span>
                <span className="text-sm font-medium text-foreground">
                  {dashboard.by_category[cat] || 0}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Heat Map */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">
          {t('page.risk_dashboard.heat_map')}
        </h3>
        <div className="overflow-x-auto">
          <table className="mx-auto">
            <thead>
              <tr>
                <th className="text-xs text-muted-foreground p-1" />
                {[1, 2, 3, 4, 5].map((i) => (
                  <th key={i} className="text-xs text-muted-foreground p-1 text-center w-14">
                    {i}
                  </th>
                ))}
              </tr>
              <tr>
                <th className="text-xs text-muted-foreground p-1" />
                <th colSpan={5} className="text-[10px] text-muted-foreground text-center pb-1">
                  {t('risk.field.impact')} →
                </th>
              </tr>
            </thead>
            <tbody>
              {[5, 4, 3, 2, 1].map((l) => (
                <tr key={l}>
                  <td className="text-xs text-muted-foreground p-1 text-right w-6">
                    {l === 3 && (
                      <span className="text-[10px] block -rotate-90 whitespace-nowrap">
                        {t('risk.field.likelihood')} →
                      </span>
                    )}
                    {l !== 3 && l}
                    {l === 3 && <span className="block">{l}</span>}
                  </td>
                  {[1, 2, 3, 4, 5].map((i) => {
                    const count = heatLookup.get(`${l},${i}`) || 0;
                    const level = levelForCell(l, i);
                    return (
                      <td key={i} className="p-0.5">
                        <div
                          className={`w-14 h-10 rounded flex items-center justify-center text-xs font-medium ${
                            count > 0 ? HEAT_COLORS[level] : 'bg-muted/30 text-muted-foreground/40'
                          }`}
                        >
                          {count > 0 ? count : ''}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Risks */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <h3 className="text-sm font-medium text-foreground">
            {t('page.risk_dashboard.recent')}
          </h3>
        </div>
        {dashboard.recent_risks.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-muted-foreground">
            {t('page.risk_dashboard.no_risks')}
          </p>
        ) : (
          <div className="divide-y divide-border">
            {dashboard.recent_risks.map((risk) => (
              <div key={risk.id} className="px-4 py-3 flex items-center justify-between">
                <div>
                  <Link to={`/risks/${risk.id}`} className="text-sm font-medium text-primary hover:underline">
                    {risk.title}
                  </Link>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {t(`risk.category.${risk.category}`)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {risk.risk_level && (
                    <Badge variant={levelVariant[risk.risk_level] || 'default'}>
                      {t(`risk.level.${risk.risk_level}`)}
                    </Badge>
                  )}
                  <Badge variant={statusVariant[risk.status] || 'default'}>
                    {t(`risk.status.${risk.status}`)}
                  </Badge>
                </div>
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
  value: number;
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
