import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Send, Loader2 } from 'lucide-react';
import { useI18n } from '../../lib/i18n';
import {
  useSupportTicketDetail,
  useAddPlatformMessage,
  useChangeTicketStatus,
  useChangeTicketPriority,
} from '../../hooks/useSupportAdmin';
import { TicketStatusBadge } from '../../components/support/TicketStatusBadge';

const VALID_TRANSITIONS: Record<string, string[]> = {
  open: ['in_progress', 'waiting_on_customer', 'resolved', 'closed'],
  in_progress: ['waiting_on_customer', 'resolved', 'closed'],
  waiting_on_customer: ['in_progress', 'resolved', 'closed'],
  resolved: ['closed'],
  closed: [],
};

const PRIORITIES = ['low', 'medium', 'high', 'urgent'];

const STATUS_ACTION_LABELS: Record<string, string> = {
  in_progress: 'support_dashboard.set_in_progress',
  waiting_on_customer: 'support_dashboard.set_waiting',
  resolved: 'support_dashboard.resolve',
  closed: 'support_dashboard.close_ticket',
};

const STATUS_ACTION_COLORS: Record<string, string> = {
  in_progress: 'bg-yellow-600 hover:bg-yellow-700',
  waiting_on_customer: 'bg-orange-600 hover:bg-orange-700',
  resolved: 'bg-green-600 hover:bg-green-700',
  closed: 'bg-gray-600 hover:bg-gray-700',
};

export default function SupportTicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const [message, setMessage] = useState('');

  const { data, isLoading, error } = useSupportTicketDetail(id || '');
  const addMessage = useAddPlatformMessage(id || '');
  const changeStatus = useChangeTicketStatus(id || '');
  const changePriority = useChangeTicketPriority(id || '');

  const ticket = data?.data;
  const allowedTransitions = ticket ? (VALID_TRANSITIONS[ticket.status] ?? []) : [];

  const handleSendMessage = () => {
    const text = message.trim();
    if (!text) return;
    addMessage.mutate(text, {
      onSuccess: () => setMessage(''),
    });
  };

  const handleStatusChange = (newStatus: string) => {
    changeStatus.mutate(newStatus);
  };

  const handlePriorityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    changePriority.mutate(e.target.value);
  };

  const formatDate = (d: string | null) => d ? new Date(d).toLocaleString() : '—';

  const formatCategory = (cat: string) => t(`support_ticket.category_${cat}` as any) || cat;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="text-center py-20 text-muted-foreground">
        Ticket not found
      </div>
    );
  }

  const isClosed = ticket.status === 'closed';

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Back link */}
      <Link
        to="/platform/support-tickets"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        {t('support_dashboard.back_to_list')}
      </Link>

      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-foreground">
            {ticket.reference} — {ticket.subject}
          </h1>
          <TicketStatusBadge status={ticket.status} />
        </div>
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          <span>Company: <span className="text-foreground">{ticket.company_id}</span></span>
          <span>Creator: <span className="text-foreground">{ticket.created_by_email || ticket.created_by}</span></span>
          <span>Category: <span className="text-foreground">{formatCategory(ticket.category)}</span></span>
          <span className="flex items-center gap-1.5">
            Priority:
            <select
              value={ticket.priority}
              onChange={handlePriorityChange}
              disabled={changePriority.isPending || isClosed}
              className="rounded border border-input bg-background px-2 py-0.5 text-sm text-foreground disabled:opacity-50"
            >
              {PRIORITIES.map(p => (
                <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
              ))}
            </select>
          </span>
        </div>
      </div>

      {/* Description */}
      <div className="rounded-lg border border-border p-4">
        <h3 className="text-sm font-medium text-foreground mb-2">{t('support_dashboard.description')}</h3>
        <p className="text-sm text-muted-foreground whitespace-pre-wrap">{ticket.description}</p>
      </div>

      {/* AI Summary */}
      {ticket.ai_conversation_summary && (
        <div className="rounded-lg border border-violet-200 bg-violet-50 p-4">
          <h3 className="text-sm font-medium text-violet-800 mb-2">AI Conversation Summary</h3>
          <p className="text-sm text-violet-700 whitespace-pre-wrap">{ticket.ai_conversation_summary}</p>
        </div>
      )}

      {/* Customer Rating */}
      {ticket.satisfaction_rating != null && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
          <h3 className="text-sm font-medium text-amber-800 mb-2">{t('support_dashboard.rating_label')}</h3>
          <div className="flex items-center gap-1 mb-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <span key={star} className={`text-lg ${star <= (ticket.satisfaction_rating ?? 0) ? 'text-amber-400' : 'text-gray-300'}`}>
                ★
              </span>
            ))}
            <span className="text-sm text-amber-700 ml-2">{ticket.satisfaction_rating} / 5</span>
          </div>
          {ticket.satisfaction_comment && (
            <p className="text-sm text-amber-700 whitespace-pre-wrap mt-2">{ticket.satisfaction_comment}</p>
          )}
          {ticket.rated_at && (
            <p className="text-xs text-amber-600 mt-1">{formatDate(ticket.rated_at)}</p>
          )}
        </div>
      )}

      {/* Conversation */}
      <div>
        <h3 className="text-sm font-medium text-foreground mb-3">{t('support_dashboard.conversation')}</h3>
        <div className="space-y-3">
          {ticket.messages.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t('support_ticket.no_messages')}</p>
          ) : (
            ticket.messages.map(msg => (
              <div
                key={msg.id}
                className={`rounded-lg p-3 ${
                  msg.is_from_platform
                    ? 'bg-primary/5 border border-primary/20 ml-8'
                    : 'bg-muted border border-border mr-8'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-foreground">
                    {msg.is_from_platform ? (
                      <span className="text-primary">{t('support_ticket.platform_team')}</span>
                    ) : (
                      msg.author_email || msg.author_name || 'Customer'
                    )}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatDate(msg.created_at)}
                  </span>
                </div>
                <p className="text-sm text-foreground whitespace-pre-wrap">{msg.body}</p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Add response */}
      {!isClosed && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-foreground">{t('support_dashboard.add_response')}</h3>
          <div className="flex gap-2">
            <textarea
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder={t('support_dashboard.response_placeholder')}
              rows={3}
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <button
            type="button"
            onClick={handleSendMessage}
            disabled={!message.trim() || addMessage.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {addMessage.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            {t('support_dashboard.send_response')}
          </button>
        </div>
      )}

      {/* Status actions */}
      {allowedTransitions.length > 0 && (
        <div className="border-t border-border pt-4">
          <h3 className="text-sm font-medium text-foreground mb-3">{t('support_dashboard.actions')}</h3>
          <div className="flex flex-wrap gap-2">
            {allowedTransitions.map(status => (
              <button
                key={status}
                type="button"
                onClick={() => handleStatusChange(status)}
                disabled={changeStatus.isPending}
                className={`inline-flex items-center rounded-md px-3 py-1.5 text-sm font-medium text-white transition-colors disabled:opacity-50 ${STATUS_ACTION_COLORS[status] || 'bg-gray-600'}`}
              >
                {t(STATUS_ACTION_LABELS[status] as any)}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Closed notice */}
      {isClosed && (
        <div className="rounded-lg bg-muted border border-border p-4 text-center text-sm text-muted-foreground">
          {t('support_ticket.closed_notice')}
        </div>
      )}
    </div>
  );
}
