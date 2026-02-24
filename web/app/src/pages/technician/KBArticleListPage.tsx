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
import { useAuthStore } from '../../stores/authStore';
import type { ArticleListItem, ArticleCategory, PaginatedResponse } from '../../types';

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger' | 'purple'> = {
  draft: 'default',
  published: 'success',
  archived: 'warning',
};

export default function KBArticleListPage() {
  const { t } = useI18n();
  const { user } = useAuthStore();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  const isTechPlus = ['technician', 'procurement_manager', 'admin', 'super_admin'].includes(user?.role || '');
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [search, setSearch] = useState('');

  const { data: categoriesData } = useQuery({
    queryKey: ['kb-categories'],
    queryFn: async () => {
      const { data } = await api.get('/kb/categories');
      return data.data as ArticleCategory[];
    },
  });

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['kb-articles', page, statusFilter, categoryId, search],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: 20 };
      if (statusFilter) params.status = statusFilter;
      if (categoryId) params.category_id = categoryId;
      if (search.trim()) params.search = search.trim();
      const { data } = await api.get('/kb/articles', { params });
      return data as PaginatedResponse<ArticleListItem>;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('page.kb.title')}</h1>
        {isTechPlus && (
          <Link to="/kb/articles/new" className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
            {t('page.kb.create_article')}
          </Link>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="search"
          placeholder={t('common.search')}
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
        />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm">
          <option value="">{t('page.kb.all_statuses')}</option>
          <option value="draft">{t('page.kb.status_draft')}</option>
          <option value="published">{t('page.kb.status_published')}</option>
          <option value="archived">{t('page.kb.status_archived')}</option>
        </select>
        <select value={categoryId} onChange={(e) => { setCategoryId(e.target.value); setPage(1); }} className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm">
          <option value="">{t('page.kb.all_categories')}</option>
          {categoriesData?.map((cat) => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>
      </div>

      {isLoading && <Loading />}
      {isError && <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />}

      {data && data.data.length === 0 && <EmptyState title={t('page.kb.no_articles')} />}

      {data && data.data.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.title')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('page.kb.category')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.status')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('page.kb.author')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('page.kb.views')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.updated')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900">
              {data.data.map((article) => (
                <tr key={article.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-4 py-3">
                    <Link to={`/kb/articles/${article.id}`} className="text-blue-600 dark:text-blue-400 hover:underline font-medium">
                      {article.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{article.category_name || '-'}</td>
                  <td className="px-4 py-3">
                    <Badge variant={statusVariant[article.status] || 'default'}>{t(`page.kb.status_${article.status}`)}</Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{article.author_name || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{article.view_count}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{formatDateTime(article.updated_at || article.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.meta.total > data.meta.page_size && (
        <Pagination page={page} pageSize={data.meta.page_size} total={data.meta.total} onChange={setPage} />
      )}
    </div>
  );
}
