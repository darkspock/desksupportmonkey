import { cn } from '../../lib/cn';
import { humanizeToken, useI18n } from '../../lib/i18n';

const variants: Record<string, string> = {
  default: 'bg-muted text-muted-foreground border-border',
  success: 'bg-success/15 text-success border-success/30',
  warning: 'bg-warning/15 text-warning-foreground border-warning/30',
  danger: 'bg-destructive/10 text-destructive border-destructive/30',
  info: 'bg-primary/10 text-primary border-primary/30',
  purple: 'bg-purple-500/10 text-purple-600 border-purple-500/30',
};

export function Badge({ children, variant = 'default' }: { children: React.ReactNode; variant?: string }) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-md border text-xs font-medium', variants[variant] || variants.default)}>
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
  draft: 'default', approved: 'success', cancelled: 'danger',
  scheduled: 'info', overdue: 'danger', skipped: 'default',
  DRAFT: 'default', DISPATCHED: 'info', IN_TRANSIT: 'warning', DELIVERED: 'success', FAILED: 'danger', CANCELLED: 'default',
};

export function StatusBadge({ status }: { status?: string | null }) {
  const { t } = useI18n();
  const normalized = typeof status === 'string' ? status.trim() : '';
  const label = normalized
    ? t(`enum.${normalized}`, undefined, { defaultValue: humanizeToken(normalized) })
    : t('common.na');

  return (
    <Badge variant={statusColors[normalized] || 'default'}>
      {label}
    </Badge>
  );
}
