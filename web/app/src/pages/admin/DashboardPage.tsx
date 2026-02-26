import { Link } from 'react-router-dom';
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
import { Badge, StatusBadge } from '../../components/ui/Badge';
import { ErrorState } from '../../components/ui/StateBlock';
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
  BudgetHealth,
  RecentPO,
  ShipmentDashboard,
  MaintenanceDashboard,
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
  const { data: reqSummary, isLoading: l1, isError: e1, error: err1 } = useQuery({
    queryKey: ['dashboard-request-summary'],
    queryFn: async () => (await api.get('/dashboard/requests/summary')).data.data as RequestSummary,
  });

  const { data: resTime, isLoading: l2, isError: e2, error: err2 } = useQuery({
    queryKey: ['dashboard-resolution-time'],
    queryFn: async () => (await api.get('/dashboard/requests/resolution-time')).data.data as ResolutionTime,
  });

  const { data: assetSummary, isLoading: l3, isError: e3, error: err3 } = useQuery({
    queryKey: ['dashboard-asset-summary'],
    queryFn: async () => (await api.get('/dashboard/assets/summary')).data.data as AssetSummary,
  });

  const { data: slaAlerts, isLoading: l4, isError: e4, error: err4 } = useQuery({
    queryKey: ['dashboard-sla'],
    queryFn: async () => (await api.get('/dashboard/alerts/sla')).data.data as SlaAlert[],
  });

  const { data: warrantyAlerts, isLoading: l5, isError: e5, error: err5 } = useQuery({
    queryKey: ['dashboard-warranty-alerts'],
    queryFn: async () => (await api.get('/dashboard/alerts/warranty', { params: { days: 30 } })).data.data as WarrantyAlert[],
  });

  const { data: agingAlerts, isLoading: l6, isError: e6, error: err6 } = useQuery({
    queryKey: ['dashboard-aging-alerts'],
    queryFn: async () => (await api.get('/dashboard/alerts/aging', { params: { years: 3 } })).data.data as AgingAlert[],
  });

  const { data: trend, isLoading: l7, isError: e7, error: err7 } = useQuery({
    queryKey: ['dashboard-request-trend'],
    queryFn: async () => (await api.get('/dashboard/requests/trend', { params: { bucket: 'week' } })).data.data as TrendResponse,
  });

  const { data: users, isLoading: l8, isError: e8, error: err8 } = useQuery({
    queryKey: ['dashboard-user-map'],
    queryFn: async () => (await api.get('/users', { params: { page: 1, page_size: 100 } })).data as PaginatedResponse<User>,
  });

  const { data: budgetHealth, isLoading: l9, isError: e9, error: err9 } = useQuery({
    queryKey: ['dashboard-budget-health'],
    queryFn: async () => (await api.get('/dashboard/budget-health')).data.data as BudgetHealth,
  });

  const { data: recentPOs, isLoading: l10, isError: e10, error: err10 } = useQuery({
    queryKey: ['dashboard-recent-pos'],
    queryFn: async () => (await api.get('/dashboard/recent-purchase-orders')).data.data as RecentPO[],
  });

  const { data: shipmentDashboard, isLoading: l11, isError: e11, error: err11 } = useQuery({
    queryKey: ['dashboard-shipments'],
    queryFn: async () => (await api.get('/dashboard/shipments/summary')).data.data as ShipmentDashboard,
  });

  const { data: maintenanceDashboard, isLoading: l12, isError: e12, error: err12 } = useQuery({
    queryKey: ['dashboard-maintenance'],
    queryFn: async () => (await api.get('/dashboard/maintenance')).data.data as MaintenanceDashboard,
  });

  const { data: checkoutDashboard, isLoading: l13, isError: e13, error: err13 } = useQuery({
    queryKey: ['dashboard-checkouts'],
    queryFn: async () => (await api.get('/dashboard/checkouts')).data.data as { open_checkouts: number; pending_acceptances: number },
  });

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
  const hasAnyError = [e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13].some(Boolean);
  const errorDetail = (err: unknown) =>
    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('errors.unexpected_detail');
  const retryAll = () => {
    window.location.reload();
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('nav.dashboard')}</h2>

      {hasAnyError && (
        <div className="rounded-lg border border-warning/30 bg-warning/10 px-4 py-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-warning">{t('page.dashboard.partial_error')}</p>
            <button
              type="button"
              onClick={retryAll}
              className="rounded-md border border-warning/40 bg-card px-3 py-1.5 text-sm font-medium text-warning hover:bg-warning/10"
            >
              {t('page.dashboard.retry_all')}
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label={t('page.dashboard.open_requests')} value={e1 ? t('common.na') : reqSummary?.total_open ?? 0} />
        <StatCard label={t('page.dashboard.resolved')} value={e1 ? t('common.na') : reqSummary?.total_resolved ?? 0} />
        <StatCard label={t('page.dashboard.avg_resolution')} value={e2 ? t('common.na') : (resTime?.avg_hours ? `${resTime.avg_hours}h` : t('common.na'))} />
        <StatCard label={t('page.dashboard.total_assets')} value={e3 ? t('common.na') : assetSummary?.total ?? 0} />
        <StatCard label={t('page.dashboard.open_checkouts')} value={e13 ? t('common.na') : checkoutDashboard?.open_checkouts ?? 0} />
        <StatCard label={t('page.dashboard.pending_acceptances')} value={e13 ? t('common.na') : checkoutDashboard?.pending_acceptances ?? 0} />
      </div>

      {(maintenanceDashboard || l12 || e12) && (
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-medium text-foreground">{t('page.dashboard.maintenance_summary')}</h3>
            <Link to="/maintenance" className="text-xs text-primary hover:underline">{t('page.dashboard.view_all_maintenance')}</Link>
          </div>
          {l12 ? (
            <Loading />
          ) : e12 ? (
            <ErrorState message={errorDetail(err12)} />
          ) : (
            <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
              <div className="rounded-lg bg-secondary p-3">
                <p className="text-xs text-muted-foreground">{t('enum.maintenance_status.scheduled')}</p>
                <p className="text-lg font-semibold text-foreground">{maintenanceDashboard?.scheduled ?? 0}</p>
              </div>
              <div className="rounded-lg bg-destructive/10 p-3">
                <p className="text-xs text-destructive">{t('page.dashboard.overdue')}</p>
                <p className="text-lg font-semibold text-destructive">{maintenanceDashboard?.overdue ?? 0}</p>
              </div>
              <div className="rounded-lg bg-warning/10 p-3">
                <p className="text-xs text-warning">{t('enum.maintenance_status.in_progress')}</p>
                <p className="text-lg font-semibold text-warning">{maintenanceDashboard?.in_progress ?? 0}</p>
              </div>
              <div className="rounded-lg bg-success/10 p-3">
                <p className="text-xs text-success">{t('page.dashboard.completed_30d')}</p>
                <p className="text-lg font-semibold text-success">{maintenanceDashboard?.completed_30d ?? 0}</p>
              </div>
            </div>
          )}
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <h3 className="text-sm font-medium text-foreground mb-4">{t('page.dashboard.requests_by_status')}</h3>
          {l1 ? (
            <Loading />
          ) : e1 ? (
            <ErrorState message={errorDetail(err1)} />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={statusData}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-medium text-foreground mb-4">{t('page.dashboard.assets_by_status')}</h3>
          {l3 ? (
            <Loading />
          ) : e3 ? (
            <ErrorState message={errorDetail(err3)} />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={assetStatusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {assetStatusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <Card>
        <h3 className="text-sm font-medium text-foreground mb-3">{t('page.dashboard.request_trend')}</h3>
        {l7 ? (
          <Loading />
        ) : e7 ? (
          <ErrorState message={errorDetail(err7)} />
        ) : !trend?.data?.length ? (
          <p className="text-sm text-muted-foreground">{t('page.dashboard.no_trend_data')}</p>
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

      {(resTime || l2 || e2 || l8 || e8) && (
        <Card>
          <h3 className="text-sm font-medium text-foreground mb-3">{t('page.dashboard.technician_performance')}</h3>
          {l2 || l8 ? (
            <Loading />
          ) : e2 || e8 ? (
            <ErrorState message={errorDetail(err2 ?? err8)} />
          ) : !(resTime && resTime.by_technician.length > 0) ? (
            <p className="text-sm text-muted-foreground">{t('common.na')}</p>
          ) : (
            <Table>
              <thead><tr><Th>{t('table.technician')}</Th><Th>{t('table.resolved')}</Th><Th>{t('table.avg_hours')}</Th></tr></thead>
              <tbody>
                {resTime.by_technician.map((perf) => (
                  <tr key={perf.technician_id}>
                    <Td>{userById.get(perf.technician_id) || perf.technician_id}</Td>
                    <Td>{perf.resolved_count}</Td>
                    <Td>{perf.avg_hours}h</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <h3 className="text-sm font-medium text-foreground mb-3">{t('page.dashboard.warranty_expiring')}</h3>
          {l5 ? (
            <Loading />
          ) : e5 ? (
            <ErrorState message={errorDetail(err5)} />
          ) : !warrantyAlerts?.length ? (
            <p className="text-sm text-muted-foreground">{t('page.dashboard.no_warranty_alerts')}</p>
          ) : (
            <Table>
              <thead><tr><Th>{t('table.asset')}</Th><Th>{t('table.serial')}</Th><Th>{t('table.warranty')}</Th><Th>{t('table.days_left')}</Th></tr></thead>
              <tbody>
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
          <h3 className="text-sm font-medium text-foreground mb-3">{t('page.dashboard.aging_assets')}</h3>
          {l6 ? (
            <Loading />
          ) : e6 ? (
            <ErrorState message={errorDetail(err6)} />
          ) : !agingAlerts?.length ? (
            <p className="text-sm text-muted-foreground">{t('page.dashboard.no_aging_assets')}</p>
          ) : (
            <Table>
              <thead><tr><Th>{t('table.asset')}</Th><Th>{t('table.serial')}</Th><Th>{t('table.purchase_date')}</Th><Th>{t('table.age')}</Th></tr></thead>
              <tbody>
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

      {(breachedAlerts.length > 0 || e4) && (
        <Card className="border-destructive/20">
          <h3 className="text-sm font-medium text-destructive mb-3">{t('page.dashboard.sla_breaches', { count: breachedAlerts.length || 0 })}</h3>
          {l4 ? (
            <Loading />
          ) : e4 ? (
            <ErrorState message={errorDetail(err4)} />
          ) : (
            <Table>
              <thead><tr><Th>{t('table.title')}</Th><Th>{t('table.priority')}</Th><Th>{t('table.assigned')}</Th><Th>{t('table.hours_open')}</Th><Th>{t('table.sla_limit')}</Th></tr></thead>
              <tbody>
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
          )}
        </Card>
      )}

      {(shipmentDashboard || l11 || e11) && (
        <Card>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-foreground">{t('page.dashboard.active_shipments')}</h3>
            <Link to="/shipments" className="text-xs text-primary hover:underline">{t('page.dashboard.view_all_shipments')}</Link>
          </div>
          {l11 ? (
            <Loading />
          ) : e11 ? (
            <ErrorState message={errorDetail(err11)} />
          ) : (
            <>
              <div className="flex gap-4 flex-wrap">
                {Object.entries(shipmentDashboard?.active_by_status ?? {}).map(([status, count]) => (
                  <div key={status} className="flex items-center gap-2">
                    <Badge variant={status === 'DRAFT' ? 'default' : status === 'DISPATCHED' ? 'info' : status === 'IN_TRANSIT' ? 'warning' : 'default'}>
                      {t(`enum.shipment_status.${status}`, undefined, { defaultValue: humanizeToken(status) })}
                    </Badge>
                    <span className="text-sm font-medium text-foreground">{count}</span>
                  </div>
                ))}
                {(shipmentDashboard?.failed_count ?? 0) > 0 && (
                  <div className="flex items-center gap-2">
                    <Badge variant="danger">{t('page.dashboard.failed_shipments')}</Badge>
                    <span className="text-sm font-medium text-destructive">{shipmentDashboard?.failed_count ?? 0}</span>
                  </div>
                )}
              </div>
              {(shipmentDashboard?.recent_deliveries ?? 0) > 0 && (
                <p className="mt-2 text-xs text-muted-foreground">{t('page.dashboard.recent_deliveries')}: {shipmentDashboard?.recent_deliveries ?? 0}</p>
              )}
            </>
          )}
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {(budgetHealth || l9 || e9) && (
          <Card>
            <h3 className="text-sm font-medium text-foreground mb-3">{t('page.dashboard.budget_health')}</h3>
            {l9 ? (
              <Loading />
            ) : e9 ? (
              <ErrorState message={errorDetail(err9)} />
            ) : (
              <>
                <div className="mb-3">
                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                    <span>{t('page.dashboard.budget_spent')}</span>
                    <span>{formatCents(budgetHealth?.total_spent_cents ?? 0)} / {formatCents(budgetHealth?.total_allocated_cents ?? 0)}</span>
                  </div>
                  <div className="w-full h-3 rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full rounded-full ${(budgetHealth?.total_allocated_cents ?? 0) > 0 && (budgetHealth?.total_spent_cents ?? 0) / (budgetHealth?.total_allocated_cents ?? 1) > 0.8 ? 'bg-destructive' : 'bg-primary'}`}
                      style={{ width: `${(budgetHealth?.total_allocated_cents ?? 0) > 0 ? Math.min((budgetHealth?.total_spent_cents ?? 0) / (budgetHealth?.total_allocated_cents ?? 1) * 100, 100) : 0}%` }}
                    />
                  </div>
                </div>
                {(budgetHealth?.departments_at_risk?.length ?? 0) > 0 && (
                  <div>
                    <p className="text-xs font-medium text-destructive mb-2">{t('page.dashboard.at_risk_departments')}</p>
                    <div className="space-y-1">
                      {(budgetHealth?.departments_at_risk ?? []).map((d) => (
                        <div key={d.department_id} className="flex justify-between text-xs bg-destructive/10 rounded px-2 py-1">
                          <span className="text-foreground">{d.department_name}</span>
                          <span className="font-medium text-destructive">{d.utilization_pct}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {(budgetHealth?.departments_at_risk?.length ?? 0) === 0 && (
                  <p className="text-xs text-muted-foreground">{t('page.dashboard.no_at_risk')}</p>
                )}
              </>
            )}
          </Card>
        )}

        {((recentPOs && recentPOs.length > 0) || l10 || e10) && (
          <Card>
            <h3 className="text-sm font-medium text-foreground mb-3">{t('page.dashboard.recent_pos')}</h3>
            {l10 ? (
              <Loading />
            ) : e10 ? (
              <ErrorState message={errorDetail(err10)} />
            ) : (
              <Table>
                <thead>
                  <tr><Th>{t('table.po_number')}</Th><Th>{t('table.vendor')}</Th><Th>{t('table.status')}</Th><Th>{t('table.amount')}</Th><Th>{t('table.date')}</Th></tr>
                </thead>
                <tbody>
                  {(recentPOs ?? []).map((po) => (
                    <tr key={po.id}>
                      <Td><Link to={`/purchase-orders/${po.id}`} className="text-primary hover:underline">{po.po_number}</Link></Td>
                      <Td>{po.vendor_name}</Td>
                      <Td><Badge variant={po.status === 'CANCELLED' ? 'danger' : po.status === 'CLOSED' ? 'default' : 'info'}>{po.status.replace('_', ' ')}</Badge></Td>
                      <Td>{formatCents(po.total_amount_cents)}</Td>
                      <Td>{po.created_at ? formatDate(po.created_at) : '—'}</Td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}

function formatCents(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}
