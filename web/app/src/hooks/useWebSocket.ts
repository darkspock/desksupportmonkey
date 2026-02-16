import { useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

type MessageHandler = (data: Record<string, unknown>) => void;

export function useWebSocket(onMessage?: MessageHandler) {
  const { token } = useAuth();
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  const connect = useCallback(() => {
    if (!token) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws?token=${token}`);

    ws.onopen = () => {
      retryRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch { /* ignore */ }
    };

    ws.onclose = () => {
      const delay = Math.min(1000 * 2 ** retryRef.current, 30000);
      retryRef.current += 1;
      setTimeout(connect, delay);
    };

    wsRef.current = ws;
  }, [token, onMessage]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  return wsRef;
}
