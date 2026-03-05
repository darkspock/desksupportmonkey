import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { TicketStatusBadge } from '../../components/support/TicketStatusBadge';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useMyTickets } from '../../hooks/useTickets';

const statusOptions = ['', 'open', 'in_progress', 'waiting_on_customer', 'resolved', 'closed'];

export default function MyTicketsPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const { t } = useI18n();

  const { data, isLoading, isError, error, refetch } = useMyTickets(page, status || undefined);

  const priorityColor: Record<string, string> = {
    low: 'text-muted-foreground',
    medium: 'text-foreground',
    high: 'text-orange-600 dark:text-orange-400',
    urgent: 'text-red-600 dark:text-red-400 font-semibold',
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {t('support_ticket.title')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('support_ticket.subtitle')}
          </p>
        </div>
        <Link
          to="/support/tickets/new"
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 12h14M12 5v14" />
          </svg>
          {t('support_ticket.create')}
        </Link>
      </div>

      {/* Filter */}
      <div className="flex gap-3">
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground"
        >
          <option value="">{t('support_ticket.all_statuses')}</option>
          {statusOptions.filter(Boolean).map((s) => (
            <option key={s} value={s}>{t(`support_ticket.status_${s}` as never)}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <Card className="overflow-hidden p-0">
        {isLoading ? (
          <div className="p-5"><Loading /></div>
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
              onRetry={() => { void refetch(); }}
            />
          </div>
        ) : !data?.data.length ? (
          <div className="p-5"><EmptyState message={t('support_ticket.empty')} /></div>
        ) : (
          <>
            <Table>
              <thead>
                <Tr>
                  <Th>{t('support_ticket.reference')}</Th>
                  <Th>{t('support_ticket.subject')}</Th>
                  <Th>{t('support_ticket.category_label')}</Th>
                  <Th>{t('support_ticket.status_label')}</Th>
                  <Th>{t('support_ticket.priority_label')}</Th>
                  <Th>{t('support_ticket.created_at')}</Th>
                </Tr>
              </thead>
              <tbody>
                {data.data.map((ticket) => (
                  <Tr key={ticket.id}>
                    <Td>
                      <Link to={`/support/tickets/${ticket.id}`} className="text-primary hover:underline font-mono text-xs">
                        {ticket.reference}
                      </Link>
                    </Td>
                    <Td>
                      <Link to={`/support/tickets/${ticket.id}`} className="hover:underline">
                        {ticket.subject}
                      </Link>
                    </Td>
                    <Td className="text-sm text-muted-foreground">
                      {t(`support_ticket.category_${ticket.category}` as never)}
                    </Td>
                    <Td><TicketStatusBadge status={ticket.status} /></Td>
                    <Td>
                      <span className={`text-sm capitalize ${priorityColor[ticket.priority] || ''}`}>
                        {t(`support_ticket.priority_${ticket.priority}` as never)}
                      </span>
                    </Td>
                    <Td className="text-sm text-muted-foreground">{formatDate(ticket.created_at)}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
            {data.meta.total > data.meta.page_size && (
              <div className="border-t border-border px-4 py-3">
                <Pagination
                  page={data.meta.page}
                  pageSize={data.meta.page_size}
                  total={data.meta.total}
                  onChange={setPage}
                />
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
