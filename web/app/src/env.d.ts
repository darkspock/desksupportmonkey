/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_WS_BASE_URL?: string;
  readonly VITE_SENTRY_DSN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface Window {
  Sentry?: {
    init: (options: {
      dsn: string;
      environment?: string;
      tracesSampleRate?: number;
    }) => void;
  };
}
