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
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-xl border border-red-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium text-red-700">{t('errors.application_error')}</p>
        <h1 className="mt-1 text-xl font-bold text-gray-900">{title}</h1>
        <p className="mt-3 text-sm text-gray-600">{detail}</p>
        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {t('common.retry')}
          </button>
          <Link
            to="/"
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            {t('common.go_home')}
          </Link>
        </div>
      </div>
    </div>
  );
}
