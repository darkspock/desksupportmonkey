import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card, StatCard } from '../../components/ui/Card';
import { Table, Th, Td } from '../../components/ui/Table';
import { StatusBadge } from '../../components/ui/Badge';
import type { RequestSummary, ResolutionTime, AssetSummary, SlaAlert } from '../../types';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6366f1', '#ec4899'];

export default function DashboardPage() {
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

  if (l1 || l2 || l3) return <Loading />;

  const statusData = reqSummary ? Object.entries(reqSummary.by_status).map(([name, value]) => ({ name, value })) : [];
  const assetStatusData = assetSummary ? Object.entries(assetSummary.by_status).map(([name, value]) => ({ name, value })) : [];
  const breachedAlerts = slaAlerts?.filter((a) => a.breached) || [];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Dashboard</h2>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Open Requests" value={reqSummary?.total_open ?? 0} />
        <StatCard label="Resolved" value={reqSummary?.total_resolved ?? 0} />
        <StatCard label="Avg Resolution" value={resTime?.avg_hours ? `${resTime.avg_hours}h` : 'N/A'} />
        <StatCard label="Total Assets" value={assetSummary?.total ?? 0} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Requests by Status</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={statusData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Assets by Status</h3>
          <ResponsiveContainer width="100%" height={250}>
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

      {/* Technician performance */}
      {resTime && resTime.by_technician.length > 0 && (
        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Technician Performance</h3>
          <Table>
            <thead><tr><Th>Technician</Th><Th>Resolved</Th><Th>Avg Hours</Th></tr></thead>
            <tbody className="divide-y divide-gray-100">
              {resTime.by_technician.map((t) => (
                <tr key={t.technician_id}>
                  <Td>{t.technician_id}</Td>
                  <Td>{t.resolved_count}</Td>
                  <Td>{t.avg_hours}h</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      {/* SLA Breaches */}
      {breachedAlerts.length > 0 && (
        <Card className="border-red-200">
          <h3 className="text-sm font-semibold text-red-700 mb-3">SLA Breaches ({breachedAlerts.length})</h3>
          <Table>
            <thead><tr><Th>Title</Th><Th>Priority</Th><Th>Hours Open</Th><Th>SLA Limit</Th></tr></thead>
            <tbody className="divide-y divide-gray-100">
              {breachedAlerts.slice(0, 10).map((a) => (
                <tr key={a.id}>
                  <Td>{a.title}</Td>
                  <Td><StatusBadge status={a.priority} /></Td>
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
