import { cn } from '../../lib/cn';
import { humanizeToken, useI18n } from '../../lib/i18n';

const variants: Record<string, string> = {
  default: 'bg-gray-100 text-gray-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-yellow-100 text-yellow-700',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
  purple: 'bg-purple-100 text-purple-700',
};

export function Badge({ children, variant = 'default' }: { children: React.ReactNode; variant?: string }) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', variants[variant] || variants.default)}>
      {children}
    </span>
  );
}

const statusColors: Record<string, string> = {
  submitted: 'info', in_review: 'warning', in_progress: 'purple', resolved: 'success', rejected: 'danger',
  in_stock: 'success', assigned: 'info', in_repair: 'warning', decommissioned: 'default',
  active: 'success', suspended: 'warning', deactivated: 'danger',
  pending: 'warning', processing: 'info', completed: 'success', failed: 'danger',
  low: 'default', medium: 'warning', high: 'danger', urgent: 'danger',
};

export function StatusBadge({ status }: { status: string }) {
  const { t } = useI18n();
  return (
    <Badge variant={statusColors[status] || 'default'}>
      {t(`enum.${status}`, undefined, { defaultValue: humanizeToken(status) })}
    </Badge>
  );
}
