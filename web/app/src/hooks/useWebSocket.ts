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

      const wsBase = import.meta.env.VITE_WS_BASE_URL;
      const wsUrl = wsBase
        ? `${wsBase}/ws?token=${encodeURIComponent(token)}`
        : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(wsUrl);

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

      ws.onerror = () => {
        // onclose handles retry/backoff; keep error handler silent to avoid noisy logs.
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      active = false;
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
      }
      const ws = wsRef.current;
      wsRef.current = null;
      if (!ws) return;

      // In React StrictMode dev, effects mount/unmount quickly; avoid closing while CONNECTING
      // to prevent "closed before the connection is established" noise.
      if (ws.readyState === WebSocket.CONNECTING) {
        ws.addEventListener('open', () => ws.close(), { once: true });
        return;
      }

      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [token, onMessage]);

  return wsRef;
}
