import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { ArticleVersion } from '../../types';

export default function KBArticleVersionsPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['kb-article-versions', id],
    queryFn: async () => {
      const { data } = await api.get(`/kb/articles/${id}/versions`);
      return data.data as ArticleVersion[];
    },
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />;

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      <div>
        <Link to={`/kb/articles/${id}`} className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-2 block">&larr; {t('page.kb.back_to_article')}</Link>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('page.kb.version_history')}</h1>
      </div>

      {data && data.length === 0 && (
        <p className="text-gray-500 dark:text-gray-400">{t('page.kb.no_versions')}</p>
      )}

      {data && data.map((version) => (
        <div key={version.id} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="font-medium text-gray-900 dark:text-white">
              {t('page.kb.version')} {version.version_number}
            </span>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {version.editor_name || version.edited_by} &middot; {formatDateTime(version.created_at)}
            </div>
          </div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{version.title}</h3>
          <details className="text-sm">
            <summary className="text-blue-600 dark:text-blue-400 cursor-pointer hover:underline">{t('page.kb.show_content')}</summary>
            <div className="mt-2 prose dark:prose-invert max-w-none text-sm border-t border-gray-200 dark:border-gray-700 pt-2" dangerouslySetInnerHTML={{ __html: version.content }} />
          </details>
        </div>
      ))}
    </div>
  );
}
