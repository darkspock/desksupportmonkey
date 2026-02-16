import type { ReactNode } from 'react';
import { useI18n } from '../../lib/i18n';

interface EmptyStateProps {
  message: string;
  action?: ReactNode;
}

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function EmptyState({ message, action }: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 px-4 py-8 text-center">
      <p className="text-sm text-gray-600">{message}</p>
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  const { t } = useI18n();

  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-4">
      <p className="text-sm text-red-700">{message || t('errors.unexpected_detail')}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100"
        >
          {t('common.retry')}
        </button>
      ) : null}
    </div>
  );
}
