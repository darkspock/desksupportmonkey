import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

export function useNotifications() {
  const { data } = useQuery({
    queryKey: ['notifications-unread'],
    queryFn: async () => {
      const { data } = await api.get('/my/notifications', { params: { page_size: 1, is_read: false } });
      return data.meta?.total ?? 0;
    },
    refetchInterval: 30000,
  });

  return { unread: data ?? 0 };
}
