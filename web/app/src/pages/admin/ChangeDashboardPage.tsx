import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { formatDateTime, formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { ChangeDashboard } from '../../types';

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  draft: 'default',
  pending_approval: 'info',
  scheduled: 'info',
  in_progress: 'info',
  implemented: 'info',
  closed: 'success',
  rejected: 'danger',
  rolled_back: 'danger',
};

const typeVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  standard: 'default',
  normal: 'info',
  emergency: 'danger',
};

const outcomeVariant: Record<string, 'success' | 'warning' | 'danger'> = {
  successful: 'success',
  partial: 'warning',
  failed: 'danger',
};

function StatCard({ label, value, color }: { label: string; value: number | string; color?: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 text-center">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${color || 'text-foreground'}`}>{value}</p>
    </div>
  );
}

function HorizontalBar({ label, value, total, variant }: { label: string; value: number; total: number; variant: string }) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  const colorMap: Record<string, string> = {
    default: 'bg-muted-foreground',
    info: 'bg-blue-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    danger: 'bg-red-500',
  };
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-32 text-right text-muted-foreground truncate">{label}</span>
      <div className="flex-1 h-5 rounded bg-muted overflow-hidden">
        <div className={`h-full rounded ${colorMap[variant] || colorMap.default}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right font-medium">{value}</span>
    </div>
  );
}

export default function ChangeDashboardPage() {
  const { t } = useI18n();

  const { data, isLoading, error } = useQuery<ChangeDashboard>({
    queryKey: ['change-dashboard'],
    queryFn: () => api.get('/changes/dashboard').then(r => r.data),
  });

  if (isLoading) return <Loading />;
  if (error || !data) return <ErrorState message={t('page.change_dashboard.error_loading')} />;

  const statusTotal = Object.values(data.status_counts).reduce((a, b) => a + b, 0);
  const typeTotal = Object.values(data.type_counts).reduce((a, b) => a + b, 0);

  const statusOrder = ['draft', 'pending_approval', 'scheduled', 'in_progress', 'implemented', 'closed', 'rejected', 'rolled_back'];
  const typeOrder = ['standard', 'normal', 'emergency'];

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.change_dashboard.title')}</h2>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <StatCard label={t('page.change_dashboard.total_open')} value={data.total_open} />
        <StatCard label={t('page.change_dashboard.pending_approval')} value={data.pending_approval} color={data.pending_approval > 0 ? 'text-blue-500' : undefined} />
        <StatCard label={t('page.change_dashboard.in_progress')} value={data.in_progress} />
        <StatCard label={t('page.change_dashboard.implemented')} value={data.implemented} />
        <StatCard label={t('page.change_dashboard.scheduled_this_week')} value={data.scheduled_this_week} />
      </div>

      {/* Rolled Back Alert */}
      {data.rolled_back_90_days > 0 && (
        <div className="rounded-lg border border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950/30 p-4 flex items-center gap-3">
          <span className="text-2xl font-bold text-red-600">{data.rolled_back_90_days}</span>
          <div>
            <p className="font-medium text-red-700 dark:text-red-400">{t('page.change_dashboard.rolled_back_alert')}</p>
            <p className="text-sm text-red-600 dark:text-red-500">{data.rolled_back_90_days} {t('page.change_dashboard.rolled_back_description')}</p>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Distribution */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-semibold text-foreground mb-4">{t('page.change_dashboard.status_distribution')}</h3>
          <div className="flex flex-col gap-2">
            {statusOrder.map(s => (
              <HorizontalBar
                key={s}
                label={t(`enum.change_status.${s}`)}
                value={data.status_counts[s] || 0}
                total={statusTotal}
                variant={statusVariant[s] || 'default'}
              />
            ))}
          </div>
        </div>

        {/* Type Distribution */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-semibold text-foreground mb-4">{t('page.change_dashboard.type_distribution')}</h3>
          <div className="flex flex-col gap-2">
            {typeOrder.map(t2 => (
              <HorizontalBar
                key={t2}
                label={t(`enum.change_type.${t2}`)}
                value={data.type_counts[t2] || 0}
                total={typeTotal}
                variant={typeVariant[t2] || 'default'}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Upcoming Scheduled Changes */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold text-foreground mb-4">{t('page.change_dashboard.upcoming_scheduled')}</h3>
        {data.upcoming_scheduled.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('page.change_dashboard.no_upcoming')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="pb-2 pr-4 text-xs font-medium uppercase text-muted-foreground">{t('page.change_dashboard.col_title')}</th>
                  <th className="pb-2 pr-4 text-xs font-medium uppercase text-muted-foreground">{t('page.change_dashboard.col_type')}</th>
                  <th className="pb-2 pr-4 text-xs font-medium uppercase text-muted-foreground">{t('page.change_dashboard.col_planned_date')}</th>
                  <th className="pb-2 text-xs font-medium uppercase text-muted-foreground">{t('page.change_dashboard.col_assigned_to')}</th>
                </tr>
              </thead>
              <tbody>
                {data.upcoming_scheduled.map(c => (
                  <tr key={c.id} className="border-b border-border/50 last:border-0">
                    <td className="py-2 pr-4">
                      <Link to={`/changes/${c.id}`} className="font-medium text-primary hover:underline">{c.title}</Link>
                    </td>
                    <td className="py-2 pr-4">
                      <Badge variant={typeVariant[c.change_type] || 'default'}>{t(`enum.change_type.${c.change_type}`)}</Badge>
                    </td>
                    <td className="py-2 pr-4">{c.planned_date ? formatDate(c.planned_date) : '—'}</td>
                    <td className="py-2">{c.assigned_to_name || c.assigned_to || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recently Implemented */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold text-foreground mb-4">{t('page.change_dashboard.recently_implemented')}</h3>
        {data.recently_implemented.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('page.change_dashboard.no_recent')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="pb-2 pr-4 text-xs font-medium uppercase text-muted-foreground">{t('page.change_dashboard.col_title')}</th>
                  <th className="pb-2 pr-4 text-xs font-medium uppercase text-muted-foreground">{t('page.change_dashboard.col_type')}</th>
                  <th className="pb-2 pr-4 text-xs font-medium uppercase text-muted-foreground">{t('page.change_dashboard.col_implemented_at')}</th>
                  <th className="pb-2 text-xs font-medium uppercase text-muted-foreground">{t('page.change_dashboard.col_outcome')}</th>
                </tr>
              </thead>
              <tbody>
                {data.recently_implemented.map(c => (
                  <tr key={c.id} className="border-b border-border/50 last:border-0">
                    <td className="py-2 pr-4">
                      <Link to={`/changes/${c.id}`} className="font-medium text-primary hover:underline">{c.title}</Link>
                    </td>
                    <td className="py-2 pr-4">
                      <Badge variant={typeVariant[c.change_type] || 'default'}>{t(`enum.change_type.${c.change_type}`)}</Badge>
                    </td>
                    <td className="py-2 pr-4">{c.implemented_at ? formatDateTime(c.implemented_at) : '—'}</td>
                    <td className="py-2">
                      {c.pir_outcome ? (
                        <Badge variant={outcomeVariant[c.pir_outcome] || 'default'}>
                          {t(`page.change_detail.pir_outcome_${c.pir_outcome}`)}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
