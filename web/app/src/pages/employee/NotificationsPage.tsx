import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import type { Notification, PaginatedResponse } from '../../types';
import { cn } from '../../lib/cn';

export default function NotificationsPage() {
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
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
  });

  const markAllRead = useMutation({
    mutationFn: () => api.patch('/my/notifications/read-all'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread'] });
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Notifications</h2>
        <button onClick={() => markAllRead.mutate()} className="text-sm text-blue-600 hover:underline">
          Mark all read
        </button>
      </div>
      <Card>
        {isLoading ? (
          <Loading />
        ) : !data?.data.length ? (
          <p className="text-sm text-gray-500">No notifications.</p>
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
                    <p className="text-xs text-gray-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                  </div>
                  {!n.is_read && (
                    <button onClick={() => markRead.mutate(n.id)} className="text-xs text-blue-600 hover:underline shrink-0">
                      Mark read
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
