import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Pagination } from '../../components/ui/Pagination';
import { Badge } from '../../components/ui/Badge';
import { useI18n } from '../../lib/i18n';
import type { AuditEntry, PaginatedResponse } from '../../types';

const HTTP_BADGE: Record<string, string> = {
  GET: 'info', POST: 'success', PUT: 'warning', PATCH: 'warning', DELETE: 'danger',
};

export default function CrossCompanyAuditPage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [action, setAction] = useState('');
  const [companyId, setCompanyId] = useState('');
  const pageSize = 20;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['super-admin-audit', page, search, action, companyId],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (search) params.search = search;
      if (action) params.action = action;
      if (companyId) params.company_id = companyId;
      const { data } = await api.get('/super-admin/audit', { params });
      return data as PaginatedResponse<AuditEntry>;
    },
  });

  const formatDate = (iso: string) => new Date(iso).toLocaleString();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('audit.superAdmin.title')}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{t('audit.superAdmin.subtitle')}</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder={t('audit.log.search_placeholder')}
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm w-64"
        />
        <input
          type="text"
          placeholder={t('audit.log.filter_action')}
          value={action}
          onChange={(e) => { setAction(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm w-48"
        />
        <input
          type="text"
          placeholder={t('audit.superAdmin.filter_company')}
          value={companyId}
          onChange={(e) => { setCompanyId(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm w-64"
        />
      </div>

      {isLoading && <Loading />}
      {isError && <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />}
      {data && data.data.length === 0 && <EmptyState title={t('audit.log.no_entries')} />}

      {data && data.data.length > 0 && (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_timestamp')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_actor')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_method')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_action')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_resource')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_status')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_ip')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {data.data.map((entry) => (
                  <tr key={entry.id}>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
                      {formatDate(entry.created_at)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white truncate max-w-[200px]">
                      {entry.actor_email}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <Badge variant={HTTP_BADGE[entry.http_method] || 'default'}>{entry.http_method}</Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{entry.action}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      <span className="font-medium">{entry.resource_type}</span>
                      {entry.resource_id && (
                        <span className="ml-1 text-gray-400 dark:text-gray-500 text-xs">{entry.resource_id.slice(0, 12)}...</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <Badge variant={entry.response_status < 400 ? 'success' : entry.response_status < 500 ? 'warning' : 'danger'}>
                        {entry.response_status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{entry.ip_address || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={pageSize} total={data.meta.total} onChange={setPage} />
        </>
      )}
    </div>
  );
}
