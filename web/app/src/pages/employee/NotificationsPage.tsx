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
      showToast({ title: t('page.notifications.error_mark_read'), variant: 'error' });
    },
  });

  const markAllRead = useMutation({
    mutationFn: () => api.patch('/my/notifications/read-all'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread'] });
      showToast({ title: t('page.notifications.success_mark_all'), variant: 'success' });
    },
    onError: () => {
      showToast({ title: t('page.notifications.error_mark_all'), variant: 'error' });
    },
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.notifications.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.notifications.subtitle')}</p>
        </div>
        <button
          onClick={() => markAllRead.mutate()}
          disabled={markAllRead.isPending}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
        >
          {markAllRead.isPending ? t('page.notifications.marking') : t('page.notifications.mark_all')}
        </button>
      </div>

      <Card className="overflow-hidden p-0">
        {isLoading ? (
          <div className="p-5"><Loading /></div>
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
              onRetry={() => { void refetch(); }}
            />
          </div>
        ) : !data?.data.length ? (
          <div className="p-5"><EmptyState message={t('page.notifications.empty')} /></div>
        ) : (
          <>
            <div className="divide-y divide-border">
              {data.data.map((n) => (
                <div
                  key={n.id}
                  className={cn('px-5 py-3.5 flex items-start gap-3', !n.is_read && 'bg-primary/5')}
                >
                  {!n.is_read && (
                    <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className={cn('text-sm', !n.is_read ? 'font-semibold text-foreground' : 'text-foreground')}>{n.title}</p>
                    <p className="text-sm text-muted-foreground truncate">{n.body}</p>
                    <p className="text-xs text-muted-foreground mt-1">{formatDateTime(n.created_at)}</p>
                  </div>
                  {!n.is_read && (
                    <button
                      onClick={() => markRead.mutate(n.id)}
                      className="text-xs text-primary hover:underline shrink-0"
                    >
                      {t('page.notifications.mark_read')}
                    </button>
                  )}
                </div>
              ))}
            </div>
            <div className="p-4">
              <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
