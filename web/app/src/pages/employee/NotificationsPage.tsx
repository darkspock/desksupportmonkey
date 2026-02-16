import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import type { Notification, PaginatedResponse } from '../../types';
import { cn } from '../../lib/cn';
import { useToast } from '../../hooks/useToast';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';

export default function NotificationsPage() {
  const [page, setPage] = useState(1);
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['notifications', page],
    queryFn: async () => {
      const { data } = await api.get('/my/notifications', { params: { page, page_size: 20 } });
      return data as PaginatedResponse<Notification>;
    },
  });

  const markRead = useMutation({
    mutationFn: (id: string) => api.patch(`/my/notifications/${id}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread'] });
    },
    onError: () => {
      showToast({
        title: t('page.notifications.error_mark_read'),
        variant: 'error',
      });
    },
  });

  const markAllRead = useMutation({
    mutationFn: () => api.patch('/my/notifications/read-all'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread'] });
      showToast({
        title: t('page.notifications.success_mark_all'),
        variant: 'success',
      });
    },
    onError: () => {
      showToast({
        title: t('page.notifications.error_mark_all'),
        variant: 'error',
      });
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">{t('page.notifications.title')}</h2>
        <button
          onClick={() => markAllRead.mutate()}
          disabled={markAllRead.isPending}
          className="text-sm text-blue-600 hover:underline disabled:opacity-50"
        >
          {markAllRead.isPending ? t('page.notifications.marking') : t('page.notifications.mark_all')}
        </button>
      </div>
      <Card>
        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => {
              void refetch();
            }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.notifications.empty')} />
        ) : (
          <>
            <div className="divide-y divide-gray-100">
              {data.data.map((n) => (
                <div
                  key={n.id}
                  className={cn('px-4 py-3 flex items-start gap-3', !n.is_read && 'bg-blue-50')}
                >
                  <div className="flex-1 min-w-0">
                    <p className={cn('text-sm', !n.is_read ? 'font-semibold text-gray-900' : 'text-gray-700')}>{n.title}</p>
                    <p className="text-sm text-gray-500 truncate">{n.body}</p>
                    <p className="text-xs text-gray-400 mt-1">{formatDateTime(n.created_at)}</p>
                  </div>
                  {!n.is_read && (
                    <button
                      onClick={() => markRead.mutate(n.id)}
                      className="text-xs text-blue-600 hover:underline shrink-0"
                    >
                      {t('page.notifications.mark_read')}
                    </button>
                  )}
                </div>
              ))}
            </div>
            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </>
        )}
      </Card>
    </div>
  );
}
