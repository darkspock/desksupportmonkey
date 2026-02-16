import { useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useWebSocket } from './useWebSocket';

export function useNotificationRealtime() {
  const queryClient = useQueryClient();

  const refreshNotificationQueries = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['notifications-unread'] });
    queryClient.invalidateQueries({ queryKey: ['notifications'] });
  }, [queryClient]);

  useWebSocket((data) => {
    const eventType = typeof data.event_type === 'string' ? data.event_type : null;

    // Dashboard websocket channel only emits notification-related events today.
    // Refreshing notification queries keeps badge and list in sync.
    if (eventType || data.title || data.body) {
      refreshNotificationQueries();
    }
  });
}
