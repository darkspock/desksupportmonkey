/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_WS_BASE_URL?: string;
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_GOOGLE_CLIENT_ID?: string;
  readonly VITE_MICROSOFT_CLIENT_ID?: string;
  readonly VITE_MICROSOFT_TENANT_ID?: string;
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
