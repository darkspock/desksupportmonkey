import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Mail } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { useI18n } from '../../lib/i18n';
import { useCreateTicket } from '../../hooks/useTickets';

const categories = [
  'bug_report',
  'feature_request',
  'billing',
  'how_to',
  'account_access',
  'other',
];

export default function CreateTicketPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const createTicket = useCreateTicket();

  const [category, setCategory] = useState('bug_report');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const aiSummary = searchParams.get('ai_summary') || undefined;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await createTicket.mutateAsync({
        category,
        subject,
        description,
        ai_conversation_summary: aiSummary,
      });
      navigate(`/support/tickets/${result.data.id}`);
    } catch {
      // Error handled by mutation
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          {t('support_ticket.create')}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {t('support_ticket.create_subtitle')}
        </p>
      </div>

      <Card className="p-6">
        <form onSubmit={(e) => { void handleSubmit(e); }} className="space-y-5">
          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              {t('support_ticket.category_label')}
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground"
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {t(`support_ticket.category_${c}` as never)}
                </option>
              ))}
            </select>
          </div>

          {/* Subject */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              {t('support_ticket.subject')}
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              maxLength={255}
              required
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder={t('support_ticket.subject_placeholder')}
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              {t('support_ticket.description')}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={6}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-y"
              placeholder={t('support_ticket.description_placeholder')}
            />
          </div>

          {/* AI Summary notice */}
          {aiSummary && (
            <div className="rounded-lg bg-violet-50 dark:bg-violet-900/20 p-3 text-sm text-violet-700 dark:text-violet-300">
              {t('support_ticket.ai_summary_attached')}
            </div>
          )}

          {/* Error */}
          {createTicket.isError && (
            <div className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {(createTicket.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to create ticket'}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={() => navigate('/support/tickets')}
              className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium border border-input bg-background text-foreground hover:bg-accent transition-colors"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={createTicket.isPending || !subject.trim() || !description.trim()}
              className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:opacity-50"
            >
              {createTicket.isPending ? t('common.loading') : t('support_ticket.submit')}
            </button>
          </div>
        </form>
      </Card>

      <p className="text-xs text-muted-foreground flex items-center gap-1">
        <Mail className="h-3 w-3" />
        {t('support_ticket.need_more_support')}{' '}
        <a
          href={`mailto:${t('help.contact_email')}`}
          className="font-medium text-primary hover:underline"
        >
          {t('help.contact_email')}
        </a>
      </p>
    </div>
  );
}
