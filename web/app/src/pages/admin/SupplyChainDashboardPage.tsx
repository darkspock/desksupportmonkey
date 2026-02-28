import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';

interface ExpiringContract {
  contract_id: string;
  vendor_id: string;
  vendor_name: string;
  title: string;
  end_date: string;
  days_remaining: number;
}

interface ConcentrationRiskItem {
  vendor_id: string;
  vendor_name: string;
  critical_count: number;
  total_critical: number;
  percentage: number;
  is_above_threshold: boolean;
}

interface DashboardData {
  total_vendors: number;
  active_vendors: number;
  vendors_by_risk_level: Record<string, number>;
  critical_ict_count: number;
  expiring_contracts_30: number;
  expiring_contracts_60: number;
  expiring_contracts_90: number;
  expiring_contracts: ExpiringContract[];
  concentration_risk_items: ConcentrationRiskItem[];
  stale_assessment_count: number;
}

const levelVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  low: 'success',
  medium: 'info',
  high: 'warning',
  critical: 'danger',
};

function StatCard({ label, value, color }: { label: string; value: number | string; color?: string }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 text-center">
      <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${color || 'text-gray-900 dark:text-white'}`}>{value}</p>
    </div>
  );
}

function RiskBar({ level, count, max }: { level: string; count: number; max: number }) {
  const colors: Record<string, string> = {
    low: 'bg-green-500',
    medium: 'bg-yellow-500',
    high: 'bg-orange-500',
    critical: 'bg-red-500',
  };
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-16 text-xs font-medium text-gray-600 dark:text-gray-400 capitalize">{level}</span>
      <div className="flex-1 h-4 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
        <div className={`h-full rounded-full ${colors[level] || 'bg-gray-400'}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">{count}</span>
    </div>
  );
}

export default function SupplyChainDashboardPage() {
  const { t } = useI18n();
  const [exportFormat, setExportFormat] = useState<'pdf' | 'csv'>('pdf');

  const { data, isLoading, error } = useQuery<DashboardData>({
    queryKey: ['supply-chain-dashboard'],
    queryFn: () => api.get('/vendors/supply-chain-dashboard').then(r => r.data),
  });

  const exportMutation = useMutation({
    mutationFn: (format: string) =>
      api.post('/vendors/risk-export', { format }).then(r => r.data),
    onSuccess: () => {
      // Export is async — notification will arrive when ready
    },
  });

  if (isLoading) return <Loading />;
  if (error || !data) return <ErrorState message={t('supply_chain.error_loading')} />;

  const maxRisk = Math.max(...Object.values(data.vendors_by_risk_level), 1);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
          {t('supply_chain.title')}
        </h1>
        <div className="flex items-center gap-2">
          <select
            value={exportFormat}
            onChange={e => setExportFormat(e.target.value as 'pdf' | 'csv')}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1.5 text-sm"
          >
            <option value="pdf">PDF</option>
            <option value="csv">CSV</option>
          </select>
          <button
            onClick={() => exportMutation.mutate(exportFormat)}
            disabled={exportMutation.isPending}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {exportMutation.isPending ? t('supply_chain.exporting') : t('supply_chain.export')}
          </button>
          {exportMutation.isSuccess && (
            <span className="text-sm text-green-600">{t('supply_chain.export_queued')}</span>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard label={t('supply_chain.total_vendors')} value={data.total_vendors} />
        <StatCard label={t('supply_chain.active_vendors')} value={data.active_vendors} color="text-green-600" />
        <StatCard label={t('supply_chain.critical_ict')} value={data.critical_ict_count} color="text-red-600" />
        <StatCard label={t('supply_chain.expiring_30')} value={data.expiring_contracts_30} color={data.expiring_contracts_30 > 0 ? 'text-orange-600' : undefined} />
        <StatCard label={t('supply_chain.stale_assessments')} value={data.stale_assessment_count} color={data.stale_assessment_count > 0 ? 'text-amber-600' : undefined} />
        <StatCard label={t('supply_chain.expiring_90')} value={data.expiring_contracts_90} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk distribution */}
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
            {t('supply_chain.risk_distribution')}
          </h2>
          <div className="space-y-3">
            {['low', 'medium', 'high', 'critical'].map(level => (
              <RiskBar key={level} level={level} count={data.vendors_by_risk_level[level] || 0} max={maxRisk} />
            ))}
          </div>
        </div>

        {/* Concentration risk */}
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
            {t('supply_chain.concentration_risk')}
          </h2>
          {data.concentration_risk_items.length === 0 ? (
            <p className="text-sm text-gray-500">{t('supply_chain.no_concentration_data')}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-2 px-2 text-xs font-medium text-gray-500">{t('supply_chain.vendor')}</th>
                    <th className="text-right py-2 px-2 text-xs font-medium text-gray-500">{t('supply_chain.critical_deps')}</th>
                    <th className="text-right py-2 px-2 text-xs font-medium text-gray-500">%</th>
                    <th className="text-center py-2 px-2 text-xs font-medium text-gray-500">{t('supply_chain.status')}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.concentration_risk_items.map(item => (
                    <tr key={item.vendor_id} className={`border-b border-gray-100 dark:border-gray-700 ${item.is_above_threshold ? 'bg-red-50 dark:bg-red-900/10' : ''}`}>
                      <td className="py-2 px-2 font-medium text-gray-900 dark:text-white">{item.vendor_name}</td>
                      <td className="py-2 px-2 text-right text-gray-600 dark:text-gray-400">{item.critical_count}/{item.total_critical}</td>
                      <td className="py-2 px-2 text-right text-gray-600 dark:text-gray-400">{(item.percentage * 100).toFixed(0)}%</td>
                      <td className="py-2 px-2 text-center">
                        {item.is_above_threshold
                          ? <Badge variant="danger">{t('supply_chain.above_threshold')}</Badge>
                          : <Badge variant="success">{t('supply_chain.ok')}</Badge>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Expiring contracts */}
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
          {t('supply_chain.expiring_contracts')}
        </h2>
        {data.expiring_contracts.length === 0 ? (
          <p className="text-sm text-gray-500">{t('supply_chain.no_expiring_contracts')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">{t('supply_chain.vendor')}</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">{t('supply_chain.contract_title')}</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">{t('supply_chain.end_date')}</th>
                  <th className="text-right py-2 px-3 text-xs font-medium text-gray-500">{t('supply_chain.days_remaining')}</th>
                </tr>
              </thead>
              <tbody>
                {data.expiring_contracts.map(c => (
                  <tr key={c.contract_id} className="border-b border-gray-100 dark:border-gray-700">
                    <td className="py-2 px-3 font-medium text-gray-900 dark:text-white">{c.vendor_name}</td>
                    <td className="py-2 px-3 text-gray-600 dark:text-gray-400">{c.title}</td>
                    <td className="py-2 px-3 text-gray-600 dark:text-gray-400">{c.end_date}</td>
                    <td className="py-2 px-3 text-right">
                      <Badge variant={c.days_remaining <= 7 ? 'danger' : c.days_remaining <= 30 ? 'warning' : 'info'}>
                        {c.days_remaining}d
                      </Badge>
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
