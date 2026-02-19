import { isRouteErrorResponse, Link, useRouteError } from 'react-router-dom';
import { useI18n } from '../../lib/i18n';

export function RouteErrorBoundary() {
  const { t } = useI18n();
  const error = useRouteError();

  let title = t('errors.unexpected_title');
  let detail = t('errors.unexpected_detail');

  if (isRouteErrorResponse(error)) {
    title = `${error.status} ${error.statusText}`;
    detail = typeof error.data === 'string' ? error.data : detail;
  } else if (error instanceof Error) {
    detail = error.message;
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-xl border border-destructive/20 bg-card p-6 shadow-sm">
        <p className="text-sm font-medium text-destructive">{t('errors.application_error')}</p>
        <h1 className="mt-1 text-xl font-semibold tracking-tight text-foreground">{title}</h1>
        <p className="mt-3 text-sm text-muted-foreground">{detail}</p>
        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
          >
            {t('common.retry')}
          </button>
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
          >
            {t('common.go_home')}
          </Link>
        </div>
      </div>
    </div>
  );
}
