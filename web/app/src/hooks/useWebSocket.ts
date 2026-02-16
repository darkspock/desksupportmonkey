import { useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';

type MessageHandler = (data: Record<string, unknown>) => void;

export function useWebSocket(onMessage?: MessageHandler) {
  const { token } = useAuth();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) return;

    let active = true;
    let retry = 0;
    let reconnectTimer: number | null = null;

    const connect = () => {
      if (!active) return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws?token=${token}`);

      ws.onopen = () => {
        retry = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data as Record<string, unknown>);
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (!active) return;
        const delay = Math.min(1000 * 2 ** retry, 30000);
        retry += 1;
        reconnectTimer = window.setTimeout(connect, delay);
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      active = false;
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
      }
      wsRef.current?.close();
    };
  }, [token, onMessage]);

  return wsRef;
}
