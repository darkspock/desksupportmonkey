import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Pagination } from '../../components/ui/Pagination';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { ArticleListItem, ArticleCategory, PaginatedResponse } from '../../types';

export default function KnowledgeBasePage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [categoryId, setCategoryId] = useState('');
  const [search, setSearch] = useState('');

  const { data: categories } = useQuery({
    queryKey: ['kb-categories'],
    queryFn: async () => {
      const { data } = await api.get('/kb/categories');
      return data.data as ArticleCategory[];
    },
  });

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['kb-public', page, categoryId, search],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: 20 };
      if (categoryId) params.category_id = categoryId;
      if (search.trim()) params.search = search.trim();
      const { data } = await api.get('/kb/public', { params });
      return data as PaginatedResponse<ArticleListItem>;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.kb.public_title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.kb.public_subtitle')}</p>
      </div>

      {/* Search & Filter */}
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
            placeholder={t('page.kb.search_articles')}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 bg-card"
          />
        </div>
        <select
          value={categoryId}
          onChange={(e) => { setCategoryId(e.target.value); setPage(1); }}
          className="w-[200px] bg-card"
        >
          <option value="">{t('page.kb.all_categories')}</option>
          {categories?.map((cat) => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>
      </div>

      {isLoading && <Loading />}
      {isError && <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />}
      {data && data.data.length === 0 && <EmptyState message={t('page.kb.no_articles_public')} />}

      {data && data.data.length > 0 && (
        <div className="grid gap-4">
          {data.data.map((article) => (
            <Link
              key={article.id}
              to={`/kb/articles/${article.id}`}
              className="rounded-lg border border-border bg-card p-5 hover:shadow-md transition-shadow"
            >
              <h3 className="text-lg font-semibold text-foreground hover:text-primary">
                {article.title}
              </h3>
              {article.excerpt && (
                <p className="text-muted-foreground text-sm mt-1 line-clamp-2">{article.excerpt}</p>
              )}
              <div className="flex items-center gap-3 mt-3 text-xs text-muted-foreground">
                {article.category_name && <span className="bg-muted px-2 py-0.5 rounded">{article.category_name}</span>}
                <span>{article.author_name}</span>
                <span>{formatDateTime(article.published_at)}</span>
                <span>{article.view_count} {t('page.kb.views')}</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {data && data.meta.total > data.meta.page_size && (
        <Pagination page={page} pageSize={data.meta.page_size} total={data.meta.total} onChange={setPage} />
      )}
    </div>
  );
}
