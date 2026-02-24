import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useAuthStore } from '../../stores/authStore';
import { useToast } from '../../components/ui/Toast';
import type { ArticleDetail } from '../../types';

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger' | 'purple'> = {
  draft: 'default',
  published: 'success',
  archived: 'warning',
};

export default function KBArticleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  const isTechPlus = ['technician', 'procurement_manager', 'admin', 'super_admin'].includes(user?.role || '');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['kb-article', id],
    queryFn: async () => {
      const { data } = await api.get(`/kb/articles/${id}`);
      return data.data as ArticleDetail;
    },
  });

  const publishMutation = useMutation({
    mutationFn: () => api.post(`/kb/articles/${id}/publish`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['kb-article', id] }); toast.success(t('page.kb.published')); },
  });

  const unpublishMutation = useMutation({
    mutationFn: () => api.post(`/kb/articles/${id}/unpublish`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['kb-article', id] }); toast.success(t('page.kb.unpublished')); },
  });

  const archiveMutation = useMutation({
    mutationFn: () => api.post(`/kb/articles/${id}/archive`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['kb-article', id] }); toast.success(t('page.kb.archived')); },
  });

  const restoreMutation = useMutation({
    mutationFn: () => api.post(`/kb/articles/${id}/restore`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['kb-article', id] }); toast.success(t('page.kb.restored')); },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/kb/articles/${id}`),
    onSuccess: () => { navigate('/kb'); toast.success(t('common.deleted')); },
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />;
  if (!data) return null;

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/kb" className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-2 block">&larr; {t('page.kb.back_to_list')}</Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{data.title}</h1>
          <div className="flex items-center gap-3 mt-2 text-sm text-gray-500 dark:text-gray-400">
            <Badge variant={statusVariant[data.status] || 'default'}>{t(`page.kb.status_${data.status}`)}</Badge>
            {data.category_name && <span>{data.category_name}</span>}
            <span>{t('page.kb.by')} {data.author_name || data.author_id}</span>
            <span>{data.view_count} {t('page.kb.views')}</span>
            {data.published_at && <span>{t('page.kb.published_on')} {formatDateTime(data.published_at)}</span>}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 flex-shrink-0">
          {isTechPlus && (
            <Link to={`/kb/articles/${id}/edit`} className="inline-flex items-center rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
              {t('common.edit')}
            </Link>
          )}
          {isAdmin && data.status === 'draft' && (
            <button onClick={() => publishMutation.mutate()} disabled={publishMutation.isPending} className="inline-flex items-center rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50">
              {t('page.kb.publish')}
            </button>
          )}
          {isAdmin && data.status === 'published' && (
            <>
              <button onClick={() => unpublishMutation.mutate()} disabled={unpublishMutation.isPending} className="inline-flex items-center rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">
                {t('page.kb.unpublish')}
              </button>
              <button onClick={() => archiveMutation.mutate()} disabled={archiveMutation.isPending} className="inline-flex items-center rounded-lg border border-orange-300 px-3 py-2 text-sm font-medium text-orange-700 hover:bg-orange-50 disabled:opacity-50">
                {t('page.kb.archive')}
              </button>
            </>
          )}
          {isAdmin && data.status === 'archived' && (
            <button onClick={() => restoreMutation.mutate()} disabled={restoreMutation.isPending} className="inline-flex items-center rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">
              {t('page.kb.restore')}
            </button>
          )}
          {isAdmin && data.status === 'draft' && (
            <button onClick={() => { if (confirm(t('page.kb.confirm_delete'))) deleteMutation.mutate(); }} disabled={deleteMutation.isPending} className="inline-flex items-center rounded-lg border border-red-300 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50">
              {t('common.delete')}
            </button>
          )}
        </div>
      </div>

      {/* Version history link */}
      {isTechPlus && (
        <Link to={`/kb/articles/${id}/versions`} className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
          {t('page.kb.view_history')}
        </Link>
      )}

      {/* Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="prose dark:prose-invert max-w-none" dangerouslySetInnerHTML={{ __html: data.content }} />
      </div>

      {/* Meta */}
      <div className="text-sm text-gray-500 dark:text-gray-400 flex gap-4">
        <span>{t('common.created')}: {formatDateTime(data.created_at)}</span>
        <span>{t('common.updated')}: {formatDateTime(data.updated_at)}</span>
      </div>
    </div>
  );
}
