import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { CustomFieldsDisplay } from '../../components/custom-fields/CustomFieldsDisplay';
import { useToast } from '../../hooks/useToast';
import { formatDateTime, formatRelativeDate } from '../../lib/date';
import { humanizeToken, useI18n } from '../../lib/i18n';
import { WorkflowIcon } from '../../components/ui/WorkflowIcon';
import { ClipboardList } from 'lucide-react';
import type { ServiceRequest, Comment, RequestEventItem, RequestChecklistItem, ChecklistProgress } from '../../types';

/* ── helper: event label ─────────────────────────────────────────── */

function requestEventLabel(
  event: RequestEventItem,
  t: (key: string, params?: Record<string, string | number>, options?: { defaultValue?: string }) => string,
): string {
  const data = (event.data ?? {}) as Record<string, unknown>;
  if (event.event_type === 'status_changed') {
    const oldStatus = typeof data.old_status === 'string' ? data.old_status : null;
    const newStatus = typeof data.new_status === 'string' ? data.new_status : null;
    if (oldStatus && newStatus) {
      return `${t('table.status')}: ${t(`enum.${oldStatus}`, undefined, { defaultValue: humanizeToken(oldStatus) })} -> ${t(`enum.${newStatus}`, undefined, { defaultValue: humanizeToken(newStatus) })}`;
    }
  }
  if (event.event_type === 'priority_changed') {
    const oldPriority = typeof data.old_priority === 'string' ? data.old_priority : null;
    const newPriority = typeof data.new_priority === 'string' ? data.new_priority : null;
    if (oldPriority && newPriority) {
      return `${t('table.priority')}: ${t(`enum.${oldPriority}`, undefined, { defaultValue: humanizeToken(oldPriority) })} -> ${t(`enum.${newPriority}`, undefined, { defaultValue: humanizeToken(newPriority) })}`;
    }
  }
  if (event.event_type === 'rejected') {
    const reason = typeof data.reason === 'string' ? data.reason : '';
    return reason ? `${t('enum.rejected')}: ${reason}` : t('enum.rejected');
  }
  return t(`page.request_detail.event_${event.event_type}`, undefined, {
    defaultValue: humanizeToken(event.event_type),
  });
}

/* ── Priority icon ───────────────────────────────────────────────── */

const PRIORITY_CONFIG: Record<string, { color: string; icon: React.ReactNode }> = {
  urgent: {
    color: 'text-red-600',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m18 15-6-6-6 6" /><path d="m18 9-6-6-6 6" />
      </svg>
    ),
  },
  high: {
    color: 'text-orange-500',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m18 15-6-6-6 6" />
      </svg>
    ),
  },
  medium: {
    color: 'text-yellow-500',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M5 12h14" />
      </svg>
    ),
  },
  low: {
    color: 'text-blue-400',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m6 9 6 6 6-6" />
      </svg>
    ),
  },
};

function PriorityIcon({ priority, t }: { priority: string; t: (key: string, params?: Record<string, string | number>, options?: { defaultValue?: string }) => string }) {
  const config = PRIORITY_CONFIG[priority] ?? PRIORITY_CONFIG.low;
  return (
    <div className={`relative group/prio ${config.color}`}>
      {config.icon}
      <span
        role="tooltip"
        className="pointer-events-none absolute -top-9 left-1/2 z-30 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-foreground px-2.5 py-1 text-xs text-background shadow-sm group-hover/prio:block"
      >
        {t(`enum.${priority}`, undefined, { defaultValue: humanizeToken(priority) })}
      </span>
    </div>
  );
}

/* ── Status progress tracker (read-only) ─────────────────────────── */

const STATUS_FLOW = ['submitted', 'in_review', 'in_progress', 'resolved'] as const;
const STATUS_FLOW_WITH_APPROVAL = ['pending_approval', 'submitted', 'in_review', 'in_progress', 'resolved'] as const;

function StatusProgressTracker({
  currentStatus,
  events,
  t,
}: {
  currentStatus: string;
  events: RequestEventItem[] | undefined;
  t: (key: string, params?: Record<string, string | number>, options?: { defaultValue?: string }) => string;
}) {
  const isRejected = currentStatus === 'rejected';
  const hadApproval = events?.some(
    (e) => e.event_type === 'status_changed' && (e.data as Record<string, unknown>)?.old_status === 'pending_approval',
  ) || currentStatus === 'pending_approval';
  const flow = hadApproval ? STATUS_FLOW_WITH_APPROVAL : STATUS_FLOW;

  const statusHistory = new Map<string, { date: string | null; actor: string | null }>();
  const createdEvent = events?.find((e) => e.event_type === 'created');
  const firstStatus = hadApproval ? 'pending_approval' : 'submitted';
  if (createdEvent) {
    statusHistory.set(firstStatus, {
      date: createdEvent.created_at ?? null,
      actor: createdEvent.performed_by_name || createdEvent.performed_by_email || null,
    });
  }
  events?.filter((e) => e.event_type === 'status_changed').forEach((e) => {
    const data = (e.data ?? {}) as Record<string, unknown>;
    const newStatus = data.new_status as string;
    if (newStatus) {
      statusHistory.set(newStatus, {
        date: e.created_at ?? null,
        actor: e.performed_by_name || e.performed_by_email || null,
      });
    }
  });

  const currentIdx = (flow as readonly string[]).indexOf(currentStatus);
  const activeIdx = isRejected ? -1 : currentIdx;

  return (
    <div className="rounded-lg border border-border bg-card px-6 py-4">
      <div className="flex items-center">
        {flow.map((status, idx) => {
          const isDone = activeIdx >= 0 && idx < activeIdx;
          const isCurrent = idx === activeIdx;
          const history = statusHistory.get(status);

          const circleClass = isDone
            ? 'bg-primary text-primary-foreground'
            : isCurrent
              ? 'border-2 border-primary bg-primary/10 text-primary'
              : 'border-2 border-muted-foreground/30 bg-background text-muted-foreground/40';

          const lineClass = isDone ? 'bg-primary' : 'bg-muted-foreground/20';

          const labelClass = isDone || isCurrent
            ? 'text-foreground font-medium'
            : 'text-muted-foreground/50';

          const tooltipLines: string[] = [];
          if (history?.date) tooltipLines.push(formatDateTime(history.date));
          if (history?.actor) tooltipLines.push(history.actor);

          return (
            <div key={status} className="flex items-center flex-1 last:flex-none">
              <div className="relative group/step flex flex-col items-center">
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-colors ${circleClass}`}>
                  {isDone ? (
                    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 6 9 17l-5-5" />
                    </svg>
                  ) : (
                    <span className="text-xs font-bold">{idx + 1}</span>
                  )}
                </div>
                <span className={`mt-1.5 text-[11px] whitespace-nowrap ${labelClass}`}>
                  {t(`enum.${status}`, undefined, { defaultValue: humanizeToken(status) })}
                </span>
                {tooltipLines.length > 0 && (
                  <span
                    role="tooltip"
                    className="pointer-events-none absolute -top-12 left-1/2 z-30 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-foreground px-2.5 py-1.5 text-xs text-background shadow-sm group-hover/step:block leading-relaxed text-center"
                  >
                    {tooltipLines.map((line, i) => (
                      <span key={i} className="block">{line}</span>
                    ))}
                  </span>
                )}
              </div>
              {idx < flow.length - 1 && (
                <div className={`h-0.5 flex-1 mx-2 rounded-full transition-colors ${lineClass}`} />
              )}
            </div>
          );
        })}
        {isRejected && (
          <div className="flex items-center flex-none ml-2">
            <div className="h-0.5 w-4 bg-destructive/40 rounded-full mx-2" />
            <div className="relative group/step flex flex-col items-center">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-destructive text-destructive-foreground">
                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 6 6 18" /><path d="m6 6 12 12" />
                </svg>
              </div>
              <span className="mt-1.5 text-[11px] whitespace-nowrap text-destructive font-medium">
                {t('enum.rejected', undefined, { defaultValue: 'Rejected' })}
              </span>
              {statusHistory.has('rejected') && (
                <span
                  role="tooltip"
                  className="pointer-events-none absolute -top-12 left-1/2 z-30 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-foreground px-2.5 py-1.5 text-xs text-background shadow-sm group-hover/step:block leading-relaxed text-center"
                >
                  {statusHistory.get('rejected')!.date && <span className="block">{formatDateTime(statusHistory.get('rejected')!.date)}</span>}
                  {statusHistory.get('rejected')!.actor && <span className="block">{statusHistory.get('rejected')!.actor}</span>}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Main component ───────────────────────────────────────────────── */

export default function MyRequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  /* ── queries ───────────────────────────────────────────────── */

  const { data: request, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['request', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}`);
      return data.data as ServiceRequest;
    },
  });

  const { data: comments } = useQuery({
    queryKey: ['request-comments', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}/comments`);
      return data.data as Comment[];
    },
  });

  const { data: requestEvents } = useQuery({
    queryKey: ['request-events', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}/events`);
      return data.data as RequestEventItem[];
    },
    enabled: !!id,
  });

  const { data: checklistData } = useQuery({
    queryKey: ['request-checklist', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}/checklist`);
      return data as { data: RequestChecklistItem[]; progress: ChecklistProgress };
    },
    enabled: !!id,
  });

  /* ── local state ───────────────────────────────────────────── */

  const [commentBody, setCommentBody] = useState('');

  /* ── mutations ─────────────────────────────────────────────── */

  const addComment = useMutation({
    mutationFn: () => api.post(`/requests/${id}/comments`, { body: commentBody }),
    onSuccess: () => {
      setCommentBody('');
      queryClient.invalidateQueries({ queryKey: ['request-comments', id] });
      showToast({ title: t('page.request_detail.comment_added'), variant: 'success' });
    },
  });

  /* ── loading / error ───────────────────────────────────────── */

  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <ErrorState
        message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
        onRetry={() => { void refetch(); }}
      />
    );
  }
  if (!request) return <ErrorState message={t('page.request_detail.not_found')} />;

  const typeIcon = request.workflow_template_icon
    ? <WorkflowIcon name={request.workflow_template_icon} className="h-6 w-6" />
    : <ClipboardList className="h-6 w-6" />;

  /* ── render ────────────────────────────────────────────────── */

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-md border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 18-6-6 6-6" /></svg>
          </button>
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">{request.title}</h2>
            <p className="mt-0.5 text-sm text-muted-foreground">{t('page.request_detail.page_subtitle')}</p>
          </div>
        </div>
      </div>

      {/* Status progress tracker (read-only) */}
      <StatusProgressTracker
        currentStatus={request.status}
        events={requestEvents}
        t={t}
      />

      {/* Two-column layout */}
      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        {/* ── Left column: main content ── */}
        <div className="space-y-6">
          {/* Request info card */}
          <div className="rounded-lg border border-border bg-card p-6 space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                {typeIcon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <StatusBadge status={request.type} />
                  {request.subtype && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-secondary text-foreground">
                      {t(`enum.${request.subtype}`, undefined, { defaultValue: request.subtype })}
                    </span>
                  )}
                  <span className="text-xs text-muted-foreground font-mono">{request.id.slice(0, 12)}</span>
                  <span className="ml-auto" />
                  <PriorityIcon priority={request.priority} t={t} />
                </div>
                <h1 className="text-xl font-bold text-foreground mb-2">{request.title}</h1>
                <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                  {request.description}
                </p>
              </div>
            </div>
            {request.custom_fields && request.custom_fields.length > 0 && (
              <div className="mt-4">
                <h3 className="mb-2 text-sm font-semibold text-foreground">{t('page.custom_fields.section_title')}</h3>
                <CustomFieldsDisplay customFields={request.custom_fields} />
              </div>
            )}
          </div>

          {/* Completed tasks (read-only, only show done items + counter) */}
          {checklistData && checklistData.data.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground">{t('page.request_detail.tasks_completed', undefined, { defaultValue: 'Tasks completed' })}</h3>
                <span className="text-xs text-muted-foreground">
                  {t('checklist.progress')
                    .replace('{{completed}}', String(checklistData.progress.completed))
                    .replace('{{total}}', String(checklistData.progress.total))}
                </span>
              </div>
              {/* Progress bar */}
              <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-300"
                  style={{
                    width: checklistData.progress.total > 0
                      ? `${(checklistData.progress.completed / checklistData.progress.total) * 100}%`
                      : '0%',
                  }}
                />
              </div>
              {/* Only completed items */}
              {checklistData.data.filter((item) => item.is_completed).length > 0 ? (
                <div className="space-y-1">
                  {checklistData.data.filter((item) => item.is_completed).map((item) => (
                    <div key={item.id} className="flex items-center gap-3 py-1.5">
                      <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded border bg-primary border-primary text-primary-foreground">
                        <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="3">
                          <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                        </svg>
                      </div>
                      <span className="flex-1 text-sm line-through text-muted-foreground">
                        {item.title}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">{t('page.request_detail.no_tasks_completed', undefined, { defaultValue: 'No tasks completed yet' })}</p>
              )}
            </div>
          )}

          {/* Conversation / Comments */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-foreground">{t('page.request_detail.comments')}</h2>

            {/* Waiting banner (employee variant) */}
            {request.status === 'waiting_for_employee' && (
              <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/50 px-4 py-3">
                <svg viewBox="0 0 24 24" className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                <span className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  {t('page.request_detail.waiting_banner_employee')}
                </span>
              </div>
            )}

            {comments?.length ? (
              <div className="space-y-3">
                {comments.map((c, idx) => {
                  const isEmployee = c.author_role === 'employee';
                  const displayName = c.author_name || c.author_email?.split('@')[0] || c.author_id;
                  const nameParts = displayName.split(/[\s.]+/);
                  const initials = nameParts.map((p) => p[0]?.toUpperCase() ?? '').join('').slice(0, 2);

                  const roleKey = c.author_role === 'employee' ? 'role_employee'
                    : c.author_role === 'admin' || c.author_role === 'super_admin' ? 'role_admin'
                    : 'role_technician';

                  const prevDate = idx > 0 ? comments[idx - 1].created_at?.split('T')[0] : null;
                  const curDate = c.created_at?.split('T')[0] ?? '';
                  const showDateSep = idx === 0 || curDate !== prevDate;

                  return (
                    <div key={c.id}>
                      {showDateSep && (
                        <div className="flex items-center gap-3 my-4">
                          <div className="flex-1 h-px bg-border" />
                          <span className="text-xs font-medium text-muted-foreground">{formatRelativeDate(c.created_at, t)}</span>
                          <div className="flex-1 h-px bg-border" />
                        </div>
                      )}
                      <div className={`flex gap-3 ${isEmployee ? 'flex-row-reverse' : ''}`}>
                        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${isEmployee ? 'bg-muted' : 'bg-primary/10'}`}>
                          <span className={`text-xs font-medium ${isEmployee ? 'text-muted-foreground' : 'text-primary'}`}>{initials}</span>
                        </div>
                        <div className={`max-w-[80%] space-y-1 ${isEmployee ? 'items-end' : ''}`}>
                          <div className={`flex items-baseline gap-2 ${isEmployee ? 'flex-row-reverse' : ''}`}>
                            <span className="text-sm font-medium text-foreground">{displayName}</span>
                            <span className={`inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium ${isEmployee ? 'bg-muted text-muted-foreground' : 'bg-primary/10 text-primary'}`}>
                              {t(`page.request_detail.${roleKey}`)}
                            </span>
                            <span className="text-xs text-muted-foreground">{formatDateTime(c.created_at)}</span>
                          </div>
                          <div className={`rounded-lg border p-3 ${isEmployee ? 'bg-muted/50 border-border' : 'bg-primary/5 border-primary/20'}`}>
                            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{c.body}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{t('page.request_detail.no_comments')}</p>
            )}

            {/* Comment form */}
            <div className="space-y-3">
              <textarea
                value={commentBody}
                onChange={(e) => setCommentBody(e.target.value)}
                placeholder={t('page.request_detail.add_comment')}
                rows={4}
                className={`w-full resize-none ${request.status === 'waiting_for_employee' ? 'ring-2 ring-amber-400 border-amber-400' : ''}`}
              />
              <div className="flex justify-end">
                <button
                  onClick={() => addComment.mutate()}
                  disabled={!commentBody.trim()}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="m22 2-7 20-4-9-9-4zM22 2 11 13" /></svg>
                  {t('page.request_detail.send')}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ── Right column: sidebar ── */}
        <div className="space-y-4">
          {/* Info card */}
          <div className="rounded-lg border border-border bg-card p-4 space-y-4">
            {/* Status (read-only) */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">{t('table.status')}</h3>
              <StatusBadge status={request.status} />
            </div>
            <div className="h-px bg-border" />

            {/* Priority (read-only) */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">{t('table.priority')}</h3>
              <StatusBadge status={request.priority} />
            </div>
            <div className="h-px bg-border" />

            {/* Requester */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">{t('page.request_detail.requester')}</h3>
              <div className="flex items-start gap-2">
                <svg viewBox="0 0 24 24" className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
                </svg>
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-foreground">
                    {request.created_by_name || request.created_by_email || request.created_by}
                  </span>
                  {request.created_by_name && request.created_by_email && (
                    <span className="text-xs text-muted-foreground">{request.created_by_email}</span>
                  )}
                </div>
              </div>
            </div>
            <div className="h-px bg-border" />

            {/* Assigned to (read-only) */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">{t('table.assigned_to')}</h3>
              {request.assigned_to ? (
                <div className="flex items-center gap-2">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10">
                    <span className="text-xs font-medium text-primary">
                      {(request.assigned_to_name || request.assigned_to_email || '?')
                        .split('@')[0]
                        .split('.')
                        .map(p => p[0]?.toUpperCase() ?? '')
                        .join('')
                        .slice(0, 2)}
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm text-foreground">
                      {request.assigned_to_name || request.assigned_to_email || request.assigned_to}
                    </span>
                    {request.assigned_to_name && request.assigned_to_email && (
                      <span className="text-xs text-muted-foreground">{request.assigned_to_email}</span>
                    )}
                  </div>
                </div>
              ) : (
                <span className="text-sm text-muted-foreground">{t('common.unassigned')}</span>
              )}
            </div>
            <div className="h-px bg-border" />

            {/* Dates */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">{t('page.request_detail.dates')}</h3>
              <div className="space-y-2">
                <div className="flex items-start gap-2 text-xs">
                  <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" />
                  </svg>
                  <div className="flex flex-col">
                    <span className="text-muted-foreground">{t('table.created')}</span>
                    <span className="text-foreground">{formatDateTime(request.created_at)}</span>
                  </div>
                </div>
                <div className="flex items-start gap-2 text-xs">
                  <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
                  </svg>
                  <div className="flex flex-col">
                    <span className="text-muted-foreground">{t('page.request_detail.updated')}</span>
                    <span className="text-foreground">{formatDateTime(request.updated_at)}</span>
                  </div>
                </div>
                {request.resolved_at && (
                  <div className="flex items-start gap-2 text-xs">
                    <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 text-success mt-0.5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><path d="m9 11 3 3L22 4" />
                    </svg>
                    <div className="flex flex-col">
                      <span className="text-muted-foreground">{t('page.request_detail.resolved_at')}</span>
                      <span className="text-foreground">{formatDateTime(request.resolved_at)}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Request History */}
          <div className="rounded-lg border border-border bg-card p-4 space-y-3">
            <h3 className="text-sm font-medium text-foreground">
              {t('page.request_detail.history', undefined, { defaultValue: 'History' })}
            </h3>
            {requestEvents && requestEvents.length > 0 ? (
              <div className="space-y-2">
                {requestEvents.map((event) => (
                  <div key={event.id} className="rounded-lg border border-border/60 bg-secondary/40 px-3 py-2">
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-xs text-foreground">
                        {requestEventLabel(event, t)}
                      </span>
                      <span className="shrink-0 text-[11px] text-muted-foreground">
                        {event.created_at ? formatDateTime(event.created_at) : '—'}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {event.performed_by_name || event.performed_by_email || event.performed_by}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                {t('page.request_detail.no_history', undefined, { defaultValue: 'No history yet' })}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
