import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { TicketStatusBadge } from '../../components/support/TicketStatusBadge';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useTicketDetail, useAddMessage, useReopenTicket, useSubmitRating } from '../../hooks/useTickets';

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const { data, isLoading, isError, error, refetch } = useTicketDetail(id || '');
  const addMessage = useAddMessage(id || '');
  const reopenTicket = useReopenTicket(id || '');
  const submitRating = useSubmitRating(id || '');
  const [messageBody, setMessageBody] = useState('');
  const [hoverRating, setHoverRating] = useState(0);
  const [selectedRating, setSelectedRating] = useState(0);
  const [ratingComment, setRatingComment] = useState('');

  if (isLoading) return <div className="p-5"><Loading /></div>;
  if (isError) return (
    <div className="p-5">
      <ErrorState
        message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
        onRetry={() => { void refetch(); }}
      />
    </div>
  );

  const ticket = data?.data;
  if (!ticket) return null;

  const isClosed = ticket.status === 'closed';
  const canReopen = ticket.status === 'resolved';
  const canRate = (ticket.status === 'resolved' || ticket.status === 'closed') && ticket.satisfaction_rating === null;
  const hasRated = ticket.satisfaction_rating !== null;

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageBody.trim()) return;
    try {
      await addMessage.mutateAsync(messageBody);
      setMessageBody('');
    } catch {
      // handled by mutation state
    }
  };

  const handleSubmitRating = async () => {
    if (selectedRating < 1) return;
    try {
      await submitRating.mutateAsync({
        rating: selectedRating,
        comment: ratingComment.trim() || undefined,
      });
    } catch {
      // handled by mutation state
    }
  };

  const handleReopen = async () => {
    try {
      await reopenTicket.mutateAsync();
    } catch {
      // handled by mutation state
    }
  };

  const priorityColor: Record<string, string> = {
    low: 'text-muted-foreground',
    medium: 'text-foreground',
    high: 'text-orange-600 dark:text-orange-400',
    urgent: 'text-red-600 dark:text-red-400 font-semibold',
  };

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      {/* Back link */}
      <Link to="/support/tickets" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1">
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        {t('support_ticket.back_to_list')}
      </Link>

      {/* Ticket info */}
      <Card className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-sm text-muted-foreground">{ticket.reference}</span>
              <TicketStatusBadge status={ticket.status} />
              <span className={`text-sm capitalize ${priorityColor[ticket.priority] || ''}`}>
                {t(`support_ticket.priority_${ticket.priority}` as never)}
              </span>
            </div>
            <h2 className="text-xl font-semibold text-foreground">{ticket.subject}</h2>
          </div>
          {canReopen && (
            <button
              type="button"
              onClick={() => { void handleReopen(); }}
              disabled={reopenTicket.isPending}
              className="inline-flex items-center justify-center rounded-md h-8 px-3 text-sm font-medium border border-input bg-background text-foreground hover:bg-accent transition-colors disabled:opacity-50"
            >
              {t('support_ticket.reopen')}
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
          <div>
            <span className="text-muted-foreground">{t('support_ticket.category_label')}:</span>{' '}
            <span className="text-foreground">{t(`support_ticket.category_${ticket.category}` as never)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">{t('support_ticket.created_at')}:</span>{' '}
            <span className="text-foreground">{formatDate(ticket.created_at)}</span>
          </div>
          {ticket.created_by_name && (
            <div>
              <span className="text-muted-foreground">{t('support_ticket.created_by')}:</span>{' '}
              <span className="text-foreground">{ticket.created_by_name}</span>
            </div>
          )}
          {ticket.resolved_at && (
            <div>
              <span className="text-muted-foreground">{t('support_ticket.resolved_at')}:</span>{' '}
              <span className="text-foreground">{formatDate(ticket.resolved_at)}</span>
            </div>
          )}
        </div>

        <div className="rounded-lg bg-muted/50 p-4 text-sm text-foreground whitespace-pre-wrap">
          {ticket.description}
        </div>

        {/* Reopen error */}
        {reopenTicket.isError && (
          <div className="mt-3 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {(reopenTicket.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to reopen ticket'}
          </div>
        )}
      </Card>

      {/* Rating section */}
      {canRate && (
        <Card className="p-6 border-amber-200 bg-amber-50/50 dark:bg-amber-900/10 dark:border-amber-800">
          <h3 className="text-lg font-semibold text-foreground mb-3">{t('support_ticket.rate_experience')}</h3>
          <div className="flex items-center gap-1 mb-3">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setSelectedRating(star)}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                className="text-2xl transition-colors focus:outline-none"
              >
                <span className={star <= (hoverRating || selectedRating) ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'}>
                  ★
                </span>
              </button>
            ))}
          </div>
          <textarea
            value={ratingComment}
            onChange={(e) => setRatingComment(e.target.value)}
            rows={2}
            maxLength={2000}
            placeholder={t('support_ticket.rating_comment_placeholder')}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y mb-3"
          />
          {submitRating.isError && (
            <div className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive mb-3">
              {(submitRating.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to submit rating'}
            </div>
          )}
          <button
            type="button"
            onClick={() => { void handleSubmitRating(); }}
            disabled={selectedRating < 1 || submitRating.isPending}
            className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:opacity-50"
          >
            {submitRating.isPending ? t('common.loading') : t('support_ticket.submit_rating')}
          </button>
        </Card>
      )}

      {hasRated && (
        <Card className="p-6 border-amber-200 bg-amber-50/50 dark:bg-amber-900/10 dark:border-amber-800">
          <h3 className="text-sm font-medium text-foreground mb-2">{t('support_ticket.your_rating')}</h3>
          <div className="flex items-center gap-1 mb-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <span key={star} className={`text-xl ${star <= (ticket.satisfaction_rating ?? 0) ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'}`}>
                ★
              </span>
            ))}
          </div>
          {ticket.satisfaction_comment && (
            <p className="text-sm text-muted-foreground whitespace-pre-wrap mb-2">{ticket.satisfaction_comment}</p>
          )}
          <p className="text-xs text-muted-foreground">{t('support_ticket.rating_submitted')}</p>
        </Card>
      )}

      {/* Messages / Conversation */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">{t('support_ticket.conversation')}</h3>

        {ticket.messages.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('support_ticket.no_messages')}</p>
        ) : (
          <div className="space-y-4">
            {ticket.messages.map((msg) => (
              <div
                key={msg.id}
                className={`rounded-lg p-4 text-sm ${
                  msg.is_from_platform
                    ? 'bg-violet-50 dark:bg-violet-900/20 border border-violet-200 dark:border-violet-800'
                    : 'bg-muted/50 border border-border'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-medium text-foreground">
                    {msg.author_name || msg.author_email || 'Unknown'}
                  </span>
                  {msg.is_from_platform && (
                    <span className="inline-flex items-center rounded-full bg-violet-100 dark:bg-violet-900/40 px-1.5 py-0.5 text-[10px] font-medium text-violet-700 dark:text-violet-300">
                      {t('support_ticket.platform_team')}
                    </span>
                  )}
                  <span className="text-xs text-muted-foreground ml-auto">{formatDate(msg.created_at)}</span>
                </div>
                <p className="text-foreground whitespace-pre-wrap">{msg.body}</p>
              </div>
            ))}
          </div>
        )}

        {/* Add message form */}
        {!isClosed && (
          <form onSubmit={(e) => { void handleSendMessage(e); }} className="mt-4 space-y-3">
            <textarea
              value={messageBody}
              onChange={(e) => setMessageBody(e.target.value)}
              rows={3}
              maxLength={10000}
              placeholder={t('support_ticket.message_placeholder')}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            />
            {addMessage.isError && (
              <div className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {(addMessage.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to send message'}
              </div>
            )}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={addMessage.isPending || !messageBody.trim()}
                className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:opacity-50"
              >
                {addMessage.isPending ? t('common.loading') : t('support_ticket.send_message')}
              </button>
            </div>
          </form>
        )}

        {isClosed && (
          <div className="mt-4 rounded-lg bg-muted p-3 text-sm text-muted-foreground text-center">
            {t('support_ticket.closed_notice')}
          </div>
        )}
      </Card>
    </div>
  );
}
