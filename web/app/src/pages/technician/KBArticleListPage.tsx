import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Pagination } from '../../components/ui/Pagination';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useAuth } from '../../contexts/AuthContext';
import type { ArticleListItem, ArticleCategory, PaginatedResponse } from '../../types';

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger' | 'purple'> = {
  draft: 'default',
  published: 'success',
  archived: 'warning',
};

export default function KBArticleListPage() {
  const { t } = useI18n();
  const { user } = useAuth();
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.kb.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.kb.subtitle')}</p>
        </div>
        {isTechPlus && (
          <Link
            to="/kb/articles/new"
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5v14" /></svg>
            {t('page.kb.create_article')}
          </Link>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <svg
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            type="search"
            placeholder={t('common.search')}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 bg-card"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="w-[150px] bg-card"
          >
            <option value="">{t('page.kb.all_statuses')}</option>
            <option value="draft">{t('page.kb.status_draft')}</option>
            <option value="published">{t('page.kb.status_published')}</option>
            <option value="archived">{t('page.kb.status_archived')}</option>
          </select>
          <select
            value={categoryId}
            onChange={(e) => { setCategoryId(e.target.value); setPage(1); }}
            className="w-[200px] bg-card"
          >
            <option value="">{t('page.kb.all_categories')}</option>
            {categoriesData?.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? <Loading /> : isError ? (
        <ErrorState
          message={(error as Error)?.message || t('common.error')}
          onRetry={() => { void refetch(); }}
        />
      ) : !data?.data.length ? (
        <EmptyState message={t('page.kb.no_articles')} />
      ) : (
        <>
          <Table>
            <thead>
              <tr className="hover:bg-transparent">
                <Th className="pl-4">{t('common.title')}</Th>
                <Th>{t('page.kb.category')}</Th>
                <Th>{t('common.status')}</Th>
                <Th className="hidden lg:table-cell">{t('page.kb.author')}</Th>
                <Th className="hidden md:table-cell">{t('page.kb.views')}</Th>
                <Th className="hidden md:table-cell">{t('common.updated')}</Th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((article) => (
                <Tr key={article.id}>
                  <Td className="pl-4">
                    <Link to={`/kb/articles/${article.id}`} className="text-sm font-medium text-foreground hover:text-primary transition-colors">
                      {article.title}
                    </Link>
                    {article.excerpt && (
                      <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">{article.excerpt}</p>
                    )}
                  </Td>
                  <Td><span className="text-sm text-muted-foreground">{article.category_name || '—'}</span></Td>
                  <Td>
                    <Badge variant={statusVariant[article.status] || 'default'}>{t(`page.kb.status_${article.status}`)}</Badge>
                  </Td>
                  <Td className="hidden lg:table-cell"><span className="text-sm text-muted-foreground">{article.author_name || '—'}</span></Td>
                  <Td className="hidden md:table-cell"><span className="text-sm text-muted-foreground">{article.view_count}</span></Td>
                  <Td className="hidden md:table-cell"><span className="text-sm text-muted-foreground">{formatDateTime(article.updated_at || article.created_at)}</span></Td>
                </Tr>
              ))}
            </tbody>
          </Table>
          {data.meta.total > data.meta.page_size && (
            <Pagination page={page} pageSize={data.meta.page_size} total={data.meta.total} onChange={setPage} />
          )}
        </>
      )}
    </div>
  );
}
