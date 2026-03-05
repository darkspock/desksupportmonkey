import { useI18n } from '../../lib/i18n';

const statusStyles: Record<string, string> = {
  open: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  waiting_on_customer: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  resolved: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  closed: 'bg-gray-100 text-gray-600 dark:bg-gray-800/40 dark:text-gray-400',
};

export function TicketStatusBadge({ status }: { status: string }) {
  const { t } = useI18n();
  const style = statusStyles[status] || statusStyles.closed;
  const label = t(`support_ticket.status_${status}` as never) || status.replace(/_/g, ' ');

  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${style}`}>
      {label}
    </span>
  );
}
