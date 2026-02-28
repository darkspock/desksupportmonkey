import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';

interface MostDependedAsset {
  asset_id: string;
  asset_name: string;
  asset_tag: string | null;
  incoming_count: number;
}

interface OverdueBIAReview {
  asset_id: string;
  asset_name: string;
  asset_tag: string | null;
  criticality: string;
  bia_reviewed_at: string | null;
}

interface CMDBDashboardData {
  criticality_distribution: Record<string, number>;
  orphan_critical_count: number;
  bia_total_critical_high: number;
  bia_has_coverage: number;
  bia_coverage_pct: number;
  total_relationships: number;
  relationships_by_type: Record<string, number>;
  most_depended_upon: MostDependedAsset[];
  overdue_bia_reviews: OverdueBIAReview[];
}

const criticalityColors: Record<string, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-green-500',
  unclassified: 'bg-gray-400',
};

const criticalityBadgeVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  critical: 'danger',
  high: 'warning',
  medium: 'info',
  low: 'success',
};

const relationshipColors: Record<string, string> = {
  runs_on: 'bg-blue-500',
  depends_on: 'bg-purple-500',
  connected_to: 'bg-teal-500',
  part_of: 'bg-indigo-500',
  backs_up: 'bg-emerald-500',
};

function StatCard({ label, value, color }: { label: string; value: number | string; color?: string }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 text-center">
      <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${color || 'text-gray-900 dark:text-white'}`}>{value}</p>
    </div>
  );
}

function HorizontalBar({ label, count, max, color }: { label: string; count: number; max: number; color: string }) {
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 text-xs font-medium text-gray-600 dark:text-gray-400 capitalize">{label}</span>
      <div className="flex-1 h-4 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">{count}</span>
    </div>
  );
}

export default function CMDBDashboardPage() {
  const { t } = useI18n();

  const { data, isLoading, error } = useQuery<CMDBDashboardData>({
    queryKey: ['cmdb-dashboard'],
    queryFn: () => api.get('/assets/cmdb-dashboard').then(r => r.data.data),
  });

  if (isLoading) return <Loading />;
  if (error || !data) return <ErrorState message={t('page.cmdb_dashboard.error_loading')} />;

  // Stat card values
  const criticalHighCount =
    (data.criticality_distribution['critical'] || 0) + (data.criticality_distribution['high'] || 0);
  const biaCoveragePctDisplay = `${data.bia_coverage_pct.toFixed(0)}%`;

  // Bar chart max values
  const criticalityLevels = ['critical', 'high', 'medium', 'low', 'unclassified'];
  const maxCriticality = Math.max(...criticalityLevels.map(l => data.criticality_distribution[l] || 0), 1);

  const relationshipTypes = ['runs_on', 'depends_on', 'connected_to', 'part_of', 'backs_up'];
  const maxRelationship = Math.max(...relationshipTypes.map(t => data.relationships_by_type[t] || 0), 1);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
        {t('page.cmdb_dashboard.title')}
      </h1>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          label={t('page.cmdb_dashboard.critical_high_count')}
          value={criticalHighCount}
          color={criticalHighCount > 0 ? 'text-red-600' : undefined}
        />
        <StatCard
          label={t('page.cmdb_dashboard.orphan_critical')}
          value={data.orphan_critical_count}
          color={data.orphan_critical_count > 0 ? 'text-orange-600' : undefined}
        />
        <StatCard
          label={t('page.cmdb_dashboard.bia_coverage')}
          value={biaCoveragePctDisplay}
          color={data.bia_coverage_pct < 50 ? 'text-amber-600' : 'text-green-600'}
        />
        <StatCard
          label={t('page.cmdb_dashboard.total_relationships')}
          value={data.total_relationships}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Criticality Distribution */}
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
            {t('page.cmdb_dashboard.criticality_distribution')}
          </h2>
          <div className="space-y-3">
            {criticalityLevels.map(level => (
              <HorizontalBar
                key={level}
                label={level}
                count={data.criticality_distribution[level] || 0}
                max={maxCriticality}
                color={criticalityColors[level] || 'bg-gray-400'}
              />
            ))}
          </div>
        </div>

        {/* CI Relationships by Type */}
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
            {t('page.cmdb_dashboard.relationships_by_type')}
          </h2>
          <div className="space-y-3">
            {relationshipTypes.map(relType => (
              <HorizontalBar
                key={relType}
                label={relType.replace(/_/g, ' ')}
                count={data.relationships_by_type[relType] || 0}
                max={maxRelationship}
                color={relationshipColors[relType] || 'bg-gray-400'}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Most Depended-Upon Assets */}
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
          {t('page.cmdb_dashboard.most_depended')}
        </h2>
        {data.most_depended_upon.length === 0 ? (
          <p className="text-sm text-gray-500">{t('page.cmdb_dashboard.no_most_depended')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">
                    {t('page.cmdb_dashboard.asset_name')}
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">
                    {t('page.cmdb_dashboard.asset_tag')}
                  </th>
                  <th className="text-right py-2 px-3 text-xs font-medium text-gray-500">
                    {t('page.cmdb_dashboard.incoming_count')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.most_depended_upon.map(asset => (
                  <tr key={asset.asset_id} className="border-b border-gray-100 dark:border-gray-700">
                    <td className="py-2 px-3 font-medium text-gray-900 dark:text-white">
                      {asset.asset_name}
                    </td>
                    <td className="py-2 px-3 text-gray-600 dark:text-gray-400">
                      {asset.asset_tag || '-'}
                    </td>
                    <td className="py-2 px-3 text-right">
                      <span className="inline-flex items-center rounded-full bg-blue-100 dark:bg-blue-900/30 px-2.5 py-0.5 text-xs font-semibold text-blue-700 dark:text-blue-300">
                        {asset.incoming_count}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Overdue BIA Reviews */}
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
          {t('page.cmdb_dashboard.overdue_bia')}
        </h2>
        {data.overdue_bia_reviews.length === 0 ? (
          <p className="text-sm text-gray-500">{t('page.cmdb_dashboard.no_overdue')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">
                    {t('page.cmdb_dashboard.asset_name')}
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">
                    {t('page.cmdb_dashboard.asset_tag')}
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">
                    {t('page.cmdb_dashboard.criticality')}
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-gray-500">
                    {t('page.cmdb_dashboard.last_reviewed')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.overdue_bia_reviews.map(review => (
                  <tr key={review.asset_id} className="border-b border-gray-100 dark:border-gray-700">
                    <td className="py-2 px-3 font-medium text-gray-900 dark:text-white">
                      {review.asset_name}
                    </td>
                    <td className="py-2 px-3 text-gray-600 dark:text-gray-400">
                      {review.asset_tag || '-'}
                    </td>
                    <td className="py-2 px-3">
                      <Badge variant={criticalityBadgeVariant[review.criticality] || 'default'}>
                        {review.criticality}
                      </Badge>
                    </td>
                    <td className="py-2 px-3 text-gray-600 dark:text-gray-400">
                      {review.bia_reviewed_at
                        ? new Date(review.bia_reviewed_at).toLocaleDateString()
                        : t('page.cmdb_dashboard.never')}
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
