import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Pagination } from '../../components/ui/Pagination';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useAuth } from '../../contexts/AuthContext';
import type { RiskListItem, PaginatedResponse } from '../../types';

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

export default function RiskListPage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('');
  const [riskLevel, setRiskLevel] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['risks', page, category, status, riskLevel],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: 20 };
      if (category) params.category = category;
      if (status) params.status = status;
      if (riskLevel) params.risk_level = riskLevel;
      const { data } = await api.get('/risks', { params });
      return data as PaginatedResponse<RiskListItem>;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.risks.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.risks.subtitle')}</p>
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            <a
              href="/api/v1/risks/export"
              download
              className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-card px-4 text-sm font-medium text-foreground hover:bg-muted/50"
            >
              {t('page.risks.export_csv')}
            </a>
            <Link
              to="/risks/new"
              className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
            >
              {t('page.risks.create')}
            </Link>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-border bg-card px-3 text-sm text-foreground"
        >
          <option value="">{t('page.risks.filter_category')}</option>
          <option value="cyber">{t('risk.category.cyber')}</option>
          <option value="operational">{t('risk.category.operational')}</option>
          <option value="compliance">{t('risk.category.compliance')}</option>
          <option value="third_party">{t('risk.category.third_party')}</option>
        </select>
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-border bg-card px-3 text-sm text-foreground"
        >
          <option value="">{t('page.risks.filter_status')}</option>
          <option value="open">{t('risk.status.open')}</option>
          <option value="under_review">{t('risk.status.under_review')}</option>
          <option value="mitigated">{t('risk.status.mitigated')}</option>
          <option value="accepted">{t('risk.status.accepted')}</option>
          <option value="closed">{t('risk.status.closed')}</option>
        </select>
        <select
          value={riskLevel}
          onChange={(e) => { setRiskLevel(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-border bg-card px-3 text-sm text-foreground"
        >
          <option value="">{t('page.risks.filter_level')}</option>
          <option value="low">{t('risk.level.low')}</option>
          <option value="medium">{t('risk.level.medium')}</option>
          <option value="high">{t('risk.level.high')}</option>
          <option value="critical">{t('risk.level.critical')}</option>
        </select>
      </div>

      {isLoading && <Loading />}
      {isError && <ErrorState message={(error as Error).message} onRetry={refetch} />}

      {data && data.data.length === 0 && (
        <EmptyState
          title={t('page.risks.empty_title')}
          description={t('page.risks.empty_description')}
        />
      )}

      {data && data.data.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  <th className="px-4 py-3">{t('risk.field.title')}</th>
                  <th className="px-4 py-3">{t('risk.field.category')}</th>
                  <th className="px-4 py-3">{t('risk.field.level')}</th>
                  <th className="px-4 py-3">{t('risk.field.status')}</th>
                  <th className="px-4 py-3">{t('risk.field.treatment')}</th>
                  <th className="px-4 py-3">{t('risk.field.owner')}</th>
                  <th className="px-4 py-3">{t('risk.field.created_at')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.data.map((risk) => (
                  <tr key={risk.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-medium">
                      <Link to={`/risks/${risk.id}`} className="text-primary hover:underline">
                        {risk.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <span className="capitalize">{t(`risk.category.${risk.category}`)}</span>
                    </td>
                    <td className="px-4 py-3">
                      {risk.risk_level ? (
                        <Badge variant={levelVariant[risk.risk_level] || 'default'}>
                          {t(`risk.level.${risk.risk_level}`)}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusVariant[risk.status] || 'default'}>
                        {t(`risk.status.${risk.status}`)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      {risk.treatment ? (
                        <span className="capitalize">{t(`risk.treatment.${risk.treatment}`)}</span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {risk.owner_name || '—'}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {risk.created_at ? formatDateTime(risk.created_at) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={data.meta.page}
            pageSize={data.meta.page_size}
            total={data.meta.total}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
