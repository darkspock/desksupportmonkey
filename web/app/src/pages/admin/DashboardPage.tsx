import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
  CartesianGrid,
} from 'recharts';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card, StatCard } from '../../components/ui/Card';
import { Table, Th, Td } from '../../components/ui/Table';
import { StatusBadge } from '../../components/ui/Badge';
import { formatDate } from '../../lib/date';
import { humanizeToken, useI18n } from '../../lib/i18n';
import type {
  RequestSummary,
  ResolutionTime,
  AssetSummary,
  SlaAlert,
  WarrantyAlert,
  AgingAlert,
  TrendBucket,
  User,
  PaginatedResponse,
} from '../../types';

interface TrendResponse {
  bucket: string;
  from_date: string;
  to_date: string;
  data: TrendBucket[];
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6366f1', '#ec4899'];

export default function DashboardPage() {
  const { t } = useI18n();
  const { data: reqSummary, isLoading: l1 } = useQuery({
    queryKey: ['dashboard-request-summary'],
    queryFn: async () => (await api.get('/dashboard/requests/summary')).data.data as RequestSummary,
  });

  const { data: resTime, isLoading: l2 } = useQuery({
    queryKey: ['dashboard-resolution-time'],
    queryFn: async () => (await api.get('/dashboard/requests/resolution-time')).data.data as ResolutionTime,
  });

  const { data: assetSummary, isLoading: l3 } = useQuery({
    queryKey: ['dashboard-asset-summary'],
    queryFn: async () => (await api.get('/dashboard/assets/summary')).data.data as AssetSummary,
  });

  const { data: slaAlerts } = useQuery({
    queryKey: ['dashboard-sla'],
    queryFn: async () => (await api.get('/dashboard/alerts/sla')).data.data as SlaAlert[],
  });

  const { data: warrantyAlerts } = useQuery({
    queryKey: ['dashboard-warranty-alerts'],
    queryFn: async () => (await api.get('/dashboard/alerts/warranty', { params: { days: 30 } })).data.data as WarrantyAlert[],
  });

  const { data: agingAlerts } = useQuery({
    queryKey: ['dashboard-aging-alerts'],
    queryFn: async () => (await api.get('/dashboard/alerts/aging', { params: { years: 3 } })).data.data as AgingAlert[],
  });

  const { data: trend } = useQuery({
    queryKey: ['dashboard-request-trend'],
    queryFn: async () => (await api.get('/dashboard/requests/trend', { params: { bucket: 'week' } })).data.data as TrendResponse,
  });

  const { data: users } = useQuery({
    queryKey: ['dashboard-user-map'],
    queryFn: async () => (await api.get('/users', { params: { page: 1, page_size: 500 } })).data as PaginatedResponse<User>,
  });

  if (l1 || l2 || l3) return <Loading />;

  const statusData = reqSummary
    ? Object.entries(reqSummary.by_status).map(([name, value]) => ({
      name: t(`enum.${name}`, undefined, { defaultValue: humanizeToken(name) }),
      value,
    }))
    : [];
  const assetStatusData = assetSummary
    ? Object.entries(assetSummary.by_status).map(([name, value]) => ({
      name: t(`enum.${name}`, undefined, { defaultValue: humanizeToken(name) }),
      value,
    }))
    : [];
  const breachedAlerts = slaAlerts?.filter((a) => a.breached) || [];
  const userById = new Map((users?.data ?? []).map((u) => [u.id, u.email]));

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">{t('nav.dashboard')}</h2>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label={t('page.dashboard.open_requests')} value={reqSummary?.total_open ?? 0} />
        <StatCard label={t('page.dashboard.resolved')} value={reqSummary?.total_resolved ?? 0} />
        <StatCard label={t('page.dashboard.avg_resolution')} value={resTime?.avg_hours ? `${resTime.avg_hours}h` : t('common.na')} />
        <StatCard label={t('page.dashboard.total_assets')} value={assetSummary?.total ?? 0} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-4">{t('page.dashboard.requests_by_status')}</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={statusData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-4">{t('page.dashboard.assets_by_status')}</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={assetStatusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                {assetStatusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('page.dashboard.request_trend')}</h3>
        {!trend?.data?.length ? (
          <p className="text-sm text-gray-500">{t('page.dashboard.no_trend_data')}</p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trend.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="total" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </Card>

      {resTime && resTime.by_technician.length > 0 && (
        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('page.dashboard.technician_performance')}</h3>
          <Table>
            <thead><tr><Th>{t('table.technician')}</Th><Th>{t('table.resolved')}</Th><Th>{t('table.avg_hours')}</Th></tr></thead>
            <tbody className="divide-y divide-gray-100">
              {resTime.by_technician.map((t) => (
                <tr key={t.technician_id}>
                  <Td>{userById.get(t.technician_id) || t.technician_id}</Td>
                  <Td>{t.resolved_count}</Td>
                  <Td>{t.avg_hours}h</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('page.dashboard.warranty_expiring')}</h3>
          {!warrantyAlerts?.length ? (
            <p className="text-sm text-gray-500">{t('page.dashboard.no_warranty_alerts')}</p>
          ) : (
            <Table>
              <thead><tr><Th>{t('table.asset')}</Th><Th>{t('table.serial')}</Th><Th>{t('table.warranty')}</Th><Th>{t('table.days_left')}</Th></tr></thead>
              <tbody className="divide-y divide-gray-100">
                {warrantyAlerts.slice(0, 10).map((a) => (
                  <tr key={a.id}>
                    <Td>{a.brand} {a.model}</Td>
                    <Td>{a.serial_number}</Td>
                    <Td>{formatDate(a.warranty_expiration)}</Td>
                    <Td>{a.days_remaining}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('page.dashboard.aging_assets')}</h3>
          {!agingAlerts?.length ? (
            <p className="text-sm text-gray-500">{t('page.dashboard.no_aging_assets')}</p>
          ) : (
            <Table>
              <thead><tr><Th>{t('table.asset')}</Th><Th>{t('table.serial')}</Th><Th>{t('table.purchase_date')}</Th><Th>{t('table.age')}</Th></tr></thead>
              <tbody className="divide-y divide-gray-100">
                {agingAlerts.slice(0, 10).map((a) => (
                  <tr key={a.id}>
                    <Td>{a.brand} {a.model}</Td>
                    <Td>{a.serial_number}</Td>
                    <Td>{formatDate(a.purchase_date)}</Td>
                    <Td>{t('page.dashboard.age_years', { years: a.age_years })}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      </div>

      {breachedAlerts.length > 0 && (
        <Card className="border-red-200">
          <h3 className="text-sm font-semibold text-red-700 mb-3">{t('page.dashboard.sla_breaches', { count: breachedAlerts.length })}</h3>
          <Table>
            <thead><tr><Th>{t('table.title')}</Th><Th>{t('table.priority')}</Th><Th>{t('table.assigned')}</Th><Th>{t('table.hours_open')}</Th><Th>{t('table.sla_limit')}</Th></tr></thead>
            <tbody className="divide-y divide-gray-100">
              {breachedAlerts.slice(0, 10).map((a) => (
                <tr key={a.id}>
                  <Td>{a.title}</Td>
                  <Td><StatusBadge status={a.priority} /></Td>
                  <Td>{a.assigned_to ? (userById.get(a.assigned_to) || a.assigned_to) : '-'}</Td>
                  <Td>{Math.round(a.hours_open)}h</Td>
                  <Td>{a.sla_threshold_hours}h</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}
    </div>
  );
}
