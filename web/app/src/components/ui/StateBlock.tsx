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
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card py-16">
      <p className="text-sm text-muted-foreground">{message}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  const { t } = useI18n();

  return (
    <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-4">
      <p className="text-sm text-destructive">{message || t('errors.unexpected_detail')}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 inline-flex items-center justify-center rounded-md h-8 px-3 text-sm font-medium border border-destructive/30 bg-card shadow-xs hover:bg-destructive/10 text-destructive transition-all"
        >
          {t('common.retry')}
        </button>
      ) : null}
    </div>
  );
}
