import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card, StatCard } from '../../components/ui/Card';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { StatusBadge } from '../../components/ui/Badge';
import { ErrorState, EmptyState } from '../../components/ui/StateBlock';
import { formatDate } from '../../lib/date';
import { humanizeToken, useI18n } from '../../lib/i18n';
import type { IncidentDashboard } from '../../types';

const SEVERITY_COLORS: Record<string, { bg: string; text: string; bar: string }> = {
  P1: { bg: 'bg-destructive/10', text: 'text-destructive', bar: '#ef4444' },
  P2: { bg: 'bg-warning/10', text: 'text-warning', bar: '#f59e0b' },
  P3: { bg: 'bg-primary/10', text: 'text-primary', bar: '#3b82f6' },
  P4: { bg: 'bg-success/10', text: 'text-success', bar: '#10b981' },
};

const TYPE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6366f1', '#ec4899'];

function formatHours(hours: number | null, na: string): string {
  if (hours === null) return na;
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 24) return `${hours}h`;
  return `${Math.round(hours / 24)}d`;
}

function formatCountdown(seconds: number): string {
  if (seconds <= 0) return 'Overdue';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h >= 24) return `${Math.floor(h / 24)}d ${h % 24}h`;
  return `${h}h ${m}m`;
}

export default function IncidentDashboardPage() {
  const { t } = useI18n();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['incident-dashboard'],
    queryFn: async () => (await api.get('/incidents/dashboard')).data as IncidentDashboard,
    refetchInterval: 60_000,
  });

  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <ErrorState
        message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
        onRetry={() => { void refetch(); }}
      />
    );
  }
  if (!data) return null;

  const typeData = Object.entries(data.by_type).map(([name, value]) => ({
    name: t(`enum.incident_type.${name}`, undefined, { defaultValue: humanizeToken(name) }),
    value,
  }));

  const na = t('common.na');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {t('page.incident_dashboard.title')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('page.incident_dashboard.subtitle')}
          </p>
        </div>
        <Link
          to="/incidents"
          className="text-sm text-primary hover:underline"
        >
          {t('page.incident_dashboard.view_all')}
        </Link>
      </div>

      {/* Top stat cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label={t('page.incident_dashboard.total_active')}
          value={data.total_active}
          colorClass="text-warning"
          bgClass="bg-warning/10"
        />
        <StatCard
          label={t('page.incident_dashboard.total_closed')}
          value={data.total_closed}
          colorClass="text-success"
          bgClass="bg-success/10"
        />
        <StatCard
          label={t('page.incident_dashboard.mttc')}
          value={formatHours(data.mttc_hours, na)}
          colorClass="text-primary"
          bgClass="bg-primary/10"
        />
        <StatCard
          label={t('page.incident_dashboard.mttr')}
          value={formatHours(data.mttr_hours, na)}
          colorClass="text-primary"
          bgClass="bg-primary/10"
        />
      </div>

      {/* Severity breakdown */}
      <Card>
        <h3 className="mb-3 text-sm font-medium text-foreground">
          {t('page.incident_dashboard.active_by_severity')}
        </h3>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {(['P1', 'P2', 'P3', 'P4'] as const).map((sev) => {
            const count = data.active_by_severity[sev] ?? 0;
            const color = SEVERITY_COLORS[sev];
            return (
              <div key={sev} className={`rounded-lg p-3 ${color.bg}`}>
                <p className={`text-xs font-medium ${color.text}`}>{sev}</p>
                <p className={`text-2xl font-bold ${color.text}`}>{count}</p>
              </div>
            );
          })}
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* Type distribution chart */}
        <Card>
          <h3 className="mb-4 text-sm font-medium text-foreground">
            {t('page.incident_dashboard.by_type')}
          </h3>
          {typeData.length === 0 ? (
            <EmptyState message={t('page.incident_dashboard.no_data')} />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={typeData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {typeData.map((_, i) => (
                    <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* Upcoming deadlines */}
        <Card>
          <h3 className="mb-4 text-sm font-medium text-foreground">
            {t('page.incident_dashboard.upcoming_deadlines')}
          </h3>
          {data.upcoming_deadlines.length === 0 ? (
            <EmptyState message={t('page.incident_dashboard.no_deadlines')} />
          ) : (
            <div className="space-y-2">
              {data.upcoming_deadlines.map((d, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="min-w-0 flex-1">
                    <Link
                      to={`/incidents/${d.incident_id}`}
                      className="text-sm font-medium text-primary hover:underline truncate block"
                    >
                      {d.incident_title}
                    </Link>
                    <p className="text-xs text-muted-foreground">
                      {t(`enum.report_type.${d.report_type}`)}
                    </p>
                  </div>
                  <div className="ml-3 shrink-0 text-right">
                    <p className={`text-sm font-semibold ${d.time_remaining_seconds < 3600 ? 'text-destructive' : d.time_remaining_seconds < 86400 ? 'text-warning' : 'text-foreground'}`}>
                      {formatCountdown(d.time_remaining_seconds)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Recent incidents */}
      <Card className="overflow-hidden p-0">
        <div className="p-4 pb-0">
          <h3 className="text-sm font-medium text-foreground">
            {t('page.incident_dashboard.recent_incidents')}
          </h3>
        </div>
        {data.recent_incidents.length === 0 ? (
          <div className="p-4">
            <EmptyState message={t('page.incident_dashboard.no_incidents')} />
          </div>
        ) : (
          <Table>
            <thead>
              <tr className="hover:bg-transparent">
                <Th className="pl-4">{t('table.title')}</Th>
                <Th>{t('table.type')}</Th>
                <Th>{t('table.severity')}</Th>
                <Th>{t('table.status')}</Th>
                <Th>{t('table.created')}</Th>
              </tr>
            </thead>
            <tbody>
              {data.recent_incidents.map((inc) => (
                <Tr key={inc.id}>
                  <Td className="pl-4">
                    <Link to={`/incidents/${inc.id}`} className="text-primary hover:underline">
                      {inc.title}
                    </Link>
                  </Td>
                  <Td>{t(`enum.incident_type.${inc.incident_type}`)}</Td>
                  <Td><StatusBadge status={inc.severity} /></Td>
                  <Td><StatusBadge status={inc.status} /></Td>
                  <Td>{formatDate(inc.created_at)}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
