import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import api from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { Badge, StatusBadge } from '../../components/ui/Badge';
import { EmployeeSearchSelect } from '../../components/ui/EmployeeSearchSelect';
import { useToast } from '../../hooks/useToast';
import { formatDateTime } from '../../lib/date';
import { humanizeToken, useI18n } from '../../lib/i18n';
import type { ServiceRequest, Comment, Note, RequestEventItem, AIClassificationData, RecentPO, Appointment, TimeSlot, Shipment, AssignableUser, PaginatedResponse, User } from '../../types';

/* ── helper components ────────────────────────────────────────────── */

interface AutoAssignmentData {
  status?: string;
  matched_assets?: { asset_type: string; asset_id: string }[];
  ai_used?: boolean;
  fallback_reasons?: string[];
  profile_id?: string;
}

function AutoAssignmentCard({ data, t }: { data: unknown; t: (key: string, params?: Record<string, string | number>, options?: { defaultValue?: string }) => string }) {
  const aa = data as AutoAssignmentData;
  const statusColors: Record<string, string> = {
    matched: 'bg-success/10 text-success',
    partial: 'bg-warning/10 text-warning',
    fallback: 'bg-secondary text-foreground',
  };
  const badgeClass = statusColors[aa.status ?? ''] ?? 'bg-secondary text-muted-foreground';
  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <h3 className="text-sm font-medium text-foreground">{t('page.request_detail.auto_assignment')}</h3>
      <div className="flex items-center gap-2">
        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${badgeClass}`}>
          {t(`page.request_detail.auto_status_${aa.status ?? 'skipped'}`, undefined, { defaultValue: humanizeToken(aa.status ?? 'skipped') })}
        </span>
        {aa.ai_used && (
          <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-chart-5/10 text-chart-5">AI</span>
        )}
      </div>
      {aa.matched_assets && aa.matched_assets.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">{t('page.request_detail.matched_assets')}</p>
          <ul className="space-y-1">
            {aa.matched_assets.map((a, i) => (
              <li key={i} className="text-xs text-foreground">
                {t(`enum.${a.asset_type}`, undefined, { defaultValue: humanizeToken(a.asset_type) })} — <span className="font-mono text-muted-foreground">{a.asset_id.slice(0, 8)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {aa.fallback_reasons && aa.fallback_reasons.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">{t('page.request_detail.fallback_reasons')}</p>
          <ul className="space-y-1">
            {aa.fallback_reasons.map((r, i) => (
              <li key={i} className="text-xs text-muted-foreground">
                {t(`page.request_detail.fallback_${r}`, undefined, { defaultValue: humanizeToken(r) })}
              </li>
            ))}
          </ul>
        </div>
      )}
      {aa.profile_id && (
        <p className="text-xs text-muted-foreground">{t('page.request_detail.profile_id')}: <span className="font-mono">{aa.profile_id.slice(0, 8)}</span></p>
      )}
    </div>
  );
}

function priorityHintLabel(hint: number | undefined, t: (key: string) => string): string {
  if (hint == null) return '—';
  if (hint <= -1) return t('page.request_detail.priority_hint_lower');
  if (hint === 0) return t('page.request_detail.priority_hint_normal');
  if (hint === 1) return t('page.request_detail.priority_hint_higher');
  return t('page.request_detail.priority_hint_critical');
}

function normalizeSlotTime(slotStart: string): string {
  if (slotStart.includes('T')) {
    const maybeDate = new Date(slotStart);
    if (!Number.isNaN(maybeDate.getTime())) {
      return `${String(maybeDate.getHours()).padStart(2, '0')}:${String(maybeDate.getMinutes()).padStart(2, '0')}:${String(maybeDate.getSeconds()).padStart(2, '0')}`;
    }
  }
  const [h = '00', m = '00', s = '00'] = slotStart.split(':');
  return `${h.padStart(2, '0')}:${m.padStart(2, '0')}:${s.padStart(2, '0')}`;
}

function formatSlotLabel(slotStart: string): string {
  const timeValue = normalizeSlotTime(slotStart);
  const [h = '00', m = '00'] = timeValue.split(':');
  return `${h}:${m}`;
}

function buildSlotDateTime(targetDate: string, slotStart: string): string {
  if (slotStart.includes('T')) return slotStart;
  return `${targetDate}T${normalizeSlotTime(slotStart)}`;
}

function AIClassificationCard({ data, t }: { data: AIClassificationData; t: (key: string, params?: Record<string, string | number>, options?: { defaultValue?: string }) => string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-medium text-foreground">{t('page.request_detail.ai_classification')}</h3>
        <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
          {t('page.request_detail.ai_classified_badge')}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
        <div className="flex justify-between gap-2 bg-secondary rounded-lg px-2 py-1">
          <span className="text-muted-foreground">{t('page.request_detail.ai_suggested_type')}</span>
          <span className="font-medium text-foreground">{data.suggested_type ? t(`enum.${data.suggested_type}`, undefined, { defaultValue: data.suggested_type }) : '—'}</span>
        </div>
        <div className="flex justify-between gap-2 bg-secondary rounded-lg px-2 py-1">
          <span className="text-muted-foreground">{t('page.request_detail.ai_suggested_subtype')}</span>
          <span className="font-medium text-foreground">{data.suggested_subtype ? t(`enum.${data.suggested_subtype}`, undefined, { defaultValue: data.suggested_subtype }) : '—'}</span>
        </div>
        <div className="flex justify-between gap-2 bg-secondary rounded-lg px-2 py-1">
          <span className="text-muted-foreground">{t('page.request_detail.ai_confidence')}</span>
          <span className="font-medium text-foreground">{data.confidence != null ? `${Math.round(data.confidence * 100)}%` : '—'}</span>
        </div>
        <div className="flex justify-between gap-2 bg-secondary rounded-lg px-2 py-1">
          <span className="text-muted-foreground">{t('page.request_detail.ai_override')}</span>
          <span className="font-medium text-foreground">{data.override_applied ? t('common.yes') : t('common.no')}</span>
        </div>
        {data.override_applied && data.user_original && (
          <div className="col-span-2 flex justify-between gap-2 bg-warning/10 rounded px-2 py-1">
            <span className="text-muted-foreground">{t('page.request_detail.ai_original')}</span>
            <span className="font-medium text-foreground">
              {t(`enum.${data.user_original.type}`, undefined, { defaultValue: data.user_original.type })}
              {data.user_original.subtype ? ` / ${t(`enum.${data.user_original.subtype}`, undefined, { defaultValue: data.user_original.subtype })}` : ''}
            </span>
          </div>
        )}
        <div className="flex justify-between gap-2 bg-secondary rounded-lg px-2 py-1">
          <span className="text-muted-foreground">{t('page.request_detail.ai_priority_hint')}</span>
          <span className="font-medium text-foreground">{priorityHintLabel(data.priority_hint, t)}</span>
        </div>
        <div className="flex justify-between gap-2 bg-secondary rounded-lg px-2 py-1">
          <span className="text-muted-foreground">{t('page.request_detail.ai_provider')}</span>
          <span className="font-medium text-foreground">{data.provider ?? '—'}</span>
        </div>
        {data.model && (
          <div className="flex justify-between gap-2 bg-secondary rounded-lg px-2 py-1">
            <span className="text-muted-foreground">{t('page.request_detail.ai_model')}</span>
            <span className="font-medium text-foreground">{data.model}</span>
          </div>
        )}
        {data.latency_ms != null && (
          <div className="flex justify-between gap-2 bg-secondary rounded-lg px-2 py-1">
            <span className="text-muted-foreground">{t('page.request_detail.ai_latency')}</span>
            <span className="font-medium text-foreground">{(data.latency_ms / 1000).toFixed(1)}s</span>
          </div>
        )}
      </div>
    </div>
  );
}

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

/* ── Type icon map ────────────────────────────────────────────────── */

const TYPE_ICONS: Record<string, React.ReactNode> = {
  incident: (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
    </svg>
  ),
  new_equipment: (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8M12 17v4" />
    </svg>
  ),
  onboarding: (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M19 8v6M22 11h-6" />
    </svg>
  ),
  repair: (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76Z" />
    </svg>
  ),
  configuration: (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ),
  access_request: (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  ),
};

/* ── Main component ───────────────────────────────────────────────── */

export default function RequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, isRole } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const isTech = isRole('technician', 'admin', 'super_admin');

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

  const { data: notes } = useQuery({
    queryKey: ['request-notes', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}/notes`);
      return data.data as Note[];
    },
    enabled: isTech,
  });

  const { data: linkedPOs } = useQuery({
    queryKey: ['request-linked-pos', id],
    queryFn: async () => {
      const { data } = await api.get('/purchase-orders', { params: { request_id: id } });
      return data.data as RecentPO[];
    },
    enabled: isTech,
  });

  const { data: appointmentsList } = useQuery({
    queryKey: ['request-appointments', id],
    queryFn: async () => {
      const { data } = await api.get('/appointments', { params: { request_id: id, page: 1, page_size: 50 } });
      return data.data as Appointment[];
    },
    enabled: isTech,
  });

  const { data: linkedShipments } = useQuery({
    queryKey: ['request-shipments', id],
    queryFn: async () => {
      const { data } = await api.get('/shipments', { params: { request_id: id, page_size: 50 } });
      return data.data as Shipment[];
    },
    enabled: isTech,
  });

  const { data: requestEvents } = useQuery({
    queryKey: ['request-events', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}/events`);
      return data.data as RequestEventItem[];
    },
    enabled: !!id,
  });

  const { data: techniciansData } = useQuery({
    queryKey: ['request-detail-technicians-options'],
    queryFn: async () => {
      const { data } = await api.get('/users', { params: { page: 1, page_size: 100, role: 'technician' } });
      return data as PaginatedResponse<User>;
    },
    enabled: isTech,
  });

  const technicianOptions: AssignableUser[] = (techniciansData?.data ?? [])
    .filter((u) => u.is_active)
    .map((u) => ({ id: u.id, email: u.email, name: u.name }));

  /* ── local state ───────────────────────────────────────────── */

  const [commentBody, setCommentBody] = useState('');
  const [noteBody, setNoteBody] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [assignUserId, setAssignUserId] = useState('');
  const [showBooking, setShowBooking] = useState(false);
  const [bookingDate, setBookingDate] = useState('');
  const [bookingSlot, setBookingSlot] = useState('');
  const [bookingDuration, setBookingDuration] = useState(60);
  const [bookingLocation, setBookingLocation] = useState('');

  const { data: availableSlots } = useQuery({
    queryKey: ['appointment-slots', request?.assigned_to, bookingDate, bookingDuration],
    queryFn: async () => {
      const { data } = await api.get(`/availability/technicians/${request!.assigned_to}/slots`, {
        params: { date: bookingDate, duration_minutes: bookingDuration },
      });
      return data.data.slots as TimeSlot[];
    },
    enabled: !!request?.assigned_to && !!bookingDate && showBooking,
  });

  useEffect(() => {
    setAssignUserId(request?.assigned_to ?? '');
  }, [request?.assigned_to]);

  /* ── mutations ─────────────────────────────────────────────── */

  const scheduleAppointment = useMutation({
    mutationFn: async () => {
      await api.post('/appointments', {
        request_id: id,
        technician_id: request!.assigned_to,
        employee_id: request!.created_by,
        scheduled_start: bookingSlot,
        duration_minutes: bookingDuration,
        location: bookingLocation || null,
      });
    },
    onSuccess: () => {
      setShowBooking(false);
      setBookingDate('');
      setBookingSlot('');
      setBookingLocation('');
      queryClient.invalidateQueries({ queryKey: ['request-appointments', id] });
      showToast({ title: t('page.request_detail.toast_scheduled'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.request_detail.error_schedule');
      showToast({ title: t('page.request_detail.error_schedule'), description: detail, variant: 'error' });
    },
  });

  const isRequestClosedForAppointments = request?.status === 'resolved' || request?.status === 'rejected';
  const canScheduleAppointment = Boolean(request?.assigned_to) && !isRequestClosedForAppointments;
  const appointmentScheduleHint = !request?.assigned_to
    ? t('page.request_detail.appointments_requires_assignment')
    : isRequestClosedForAppointments
      ? t('page.request_detail.appointments_closed_no_schedule')
      : '';

  const approveRequest = useMutation({
    mutationFn: () => api.post(`/requests/${id}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request', id] });
      showToast({ title: t('page.request_detail.toast_approved'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.request_detail.error_approve');
      showToast({ title: t('page.request_detail.error_approve'), description: detail, variant: 'error' });
    },
  });

  const rejectRequest = useMutation({
    mutationFn: () => api.post(`/requests/${id}/reject`, { reason: rejectReason }),
    onSuccess: () => {
      setRejectReason('');
      setShowRejectForm(false);
      queryClient.invalidateQueries({ queryKey: ['request', id] });
      showToast({ title: t('page.request_detail.toast_rejected'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.request_detail.error_reject');
      showToast({ title: t('page.request_detail.error_reject'), description: detail, variant: 'error' });
    },
  });

  const addComment = useMutation({
    mutationFn: () => api.post(`/requests/${id}/comments`, { body: commentBody }),
    onSuccess: () => {
      setCommentBody('');
      queryClient.invalidateQueries({ queryKey: ['request-comments', id] });
      showToast({ title: t('page.request_detail.comment_added'), variant: 'success' });
    },
  });

  const addNote = useMutation({
    mutationFn: () => api.post(`/requests/${id}/notes`, { body: noteBody }),
    onSuccess: () => {
      setNoteBody('');
      queryClient.invalidateQueries({ queryKey: ['request-notes', id] });
      showToast({ title: t('page.request_detail.note_added'), variant: 'success' });
    },
  });

  const changeStatus = useMutation({
    mutationFn: (status: string) => api.patch(`/requests/${id}/status`, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request', id] });
      showToast({ title: t('page.request_detail.status_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.request_detail.error_generic');
      showToast({ title: t('page.request_detail.error_status_update'), description: detail, variant: 'error' });
    },
  });

  const changePriority = useMutation({
    mutationFn: (priority: string) => api.patch(`/requests/${id}/priority`, { priority }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request', id] });
      showToast({ title: t('page.request_detail.priority_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.request_detail.error_generic');
      showToast({ title: t('page.request_detail.error_priority_update'), description: detail, variant: 'error' });
    },
  });

  const assign = useMutation({
    mutationFn: (targetUserId: string) => api.patch(`/requests/${id}/assign`, { user_id: targetUserId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request', id] });
      showToast({ title: t('page.request_detail.assigned'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.request_detail.error_generic');
      showToast({ title: detail, variant: 'error' });
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

  const statusActions: Record<string, string[]> = {
    submitted: ['in_review', 'rejected'],
    in_review: ['in_progress', 'rejected'],
    in_progress: ['resolved'],
    rejected: ['submitted'],
  };
  const nextStatuses = statusActions[request.status] || [];
  const userNextStatusByFlow: Record<string, string | undefined> = {
    pending_approval: 'submitted',
    submitted: 'in_review',
    in_review: 'in_progress',
    in_progress: 'resolved',
  };
  const userNextStatus = userNextStatusByFlow[request.status];
  const isPendingApproval = request.status === 'pending_approval';
  const typeIcon = TYPE_ICONS[request.type];

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

      {/* Two-column layout */}
      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        {/* ── Left column: main content ── */}
        <div className="space-y-6">
          {/* Request info card */}
          <div className="rounded-lg border border-border bg-card p-6 space-y-4">
            <div className="flex items-start gap-3">
              {typeIcon && (
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  {typeIcon}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <StatusBadge status={request.type} />
                  {request.subtype && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-secondary text-foreground">
                      {t(`enum.${request.subtype}`)}
                    </span>
                  )}
                  <span className="text-xs text-muted-foreground font-mono">{request.id.slice(0, 12)}</span>
                </div>
                <h1 className="text-xl font-bold text-foreground mb-2">{request.title}</h1>
                <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                  {request.description}
                </p>
              </div>
            </div>
          </div>

          {/* Conversation / Comments */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-foreground">{t('page.request_detail.comments')}</h2>

            {comments?.length ? (
              <div className="space-y-4">
                {comments.map((c) => {
                  const initials = (c.author_email || c.author_id || '?')
                    .split('@')[0]
                    .split('.')
                    .map((part) => part[0]?.toUpperCase() ?? '')
                    .join('')
                    .slice(0, 2);
                  return (
                    <div key={c.id} className="flex gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                        <span className="text-xs font-medium text-primary">{initials}</span>
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-baseline gap-2">
                          <span className="text-sm font-medium text-foreground">{c.author_email || c.author_id}</span>
                          <span className="text-xs text-muted-foreground">{formatDateTime(c.created_at)}</span>
                        </div>
                        <div className="rounded-lg border border-border bg-card p-3">
                          <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{c.body}</p>
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
                className="w-full resize-none"
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

          {/* Internal notes (tech only) */}
          {isTech && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-foreground">{t('page.request_detail.internal_notes')}</h2>
              {notes?.length ? (
                <div className="space-y-4">
                  {notes.map((n) => {
                    const initials = (n.author_email || n.author_id || '?')
                      .split('@')[0]
                      .split('.')
                      .map((part) => part[0]?.toUpperCase() ?? '')
                      .join('')
                      .slice(0, 2);
                    return (
                      <div key={n.id} className="flex gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-warning/15">
                          <span className="text-xs font-medium text-warning-foreground">{initials}</span>
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-baseline gap-2">
                            <span className="text-sm font-medium text-foreground">{n.author_email || n.author_id}</span>
                            <span className="text-xs text-muted-foreground">{formatDateTime(n.created_at)}</span>
                          </div>
                          <div className="rounded-lg border border-warning/20 bg-warning/5 p-3">
                            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{n.body}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">{t('page.request_detail.no_internal_notes')}</p>
              )}
              <div className="space-y-3">
                <textarea
                  value={noteBody}
                  onChange={(e) => setNoteBody(e.target.value)}
                  placeholder={t('page.request_detail.add_internal_note')}
                  rows={4}
                  className="w-full resize-none"
                />
                <div className="flex justify-end">
                  <button
                    onClick={() => addNote.mutate()}
                    disabled={!noteBody.trim()}
                    className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-warning text-white shadow-xs hover:bg-warning/90 disabled:opacity-50"
                  >
                    {t('page.request_detail.add_note')}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── Right column: sidebar ── */}
        <div className="space-y-4">
          {/* Info card */}
          <div className="rounded-lg border border-border bg-card p-4 space-y-4">
            {/* Status */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">{t('table.status')}</h3>
              {!isTech && userNextStatus ? (
                <div className="flex items-center gap-2">
                  <StatusBadge status={request.status} />
                  <svg
                    viewBox="0 0 24 24"
                    className="h-3.5 w-3.5 text-muted-foreground"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M5 12h14" />
                    <path d="m13 6 6 6-6 6" />
                  </svg>
                  <span className="inline-flex items-center rounded-md border border-dashed border-muted-foreground/60 bg-white px-2 py-0.5 text-xs font-medium text-muted-foreground/90">
                    {t(`enum.${userNextStatus}`, undefined, { defaultValue: humanizeToken(userNextStatus) })}
                  </span>
                </div>
              ) : (
                <StatusBadge status={request.status} />
              )}
            </div>
            <div className="h-px bg-border" />

            {/* Priority */}
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

            {/* Assigned to */}
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

              {isTech && !isPendingApproval && (
                <div className="mt-2 flex items-center gap-2">
                  <EmployeeSearchSelect
                    users={technicianOptions}
                    value={assignUserId}
                    onChange={setAssignUserId}
                    placeholder={t('page.maintenance_detail.assign_placeholder')}
                    allLabel={t('page.asset_list.all_assignees')}
                    noResultsLabel={t('page.asset_list.no_assignee_results')}
                    className="min-w-0 flex-1"
                  />
                  <button
                    onClick={() => assign.mutate(assignUserId || user?.id || '')}
                    disabled={assign.isPending || (!assignUserId && !user?.id)}
                    className="inline-flex h-9 items-center justify-center rounded-md px-3 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                  >
                    {t('page.maintenance_detail.assign')}
                  </button>
                </div>
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

          {/* Actions card (tech only, non-terminal statuses) */}
          {isTech && (nextStatuses.length > 0 || isPendingApproval) && (
            <div className="rounded-lg border border-border bg-card p-4 space-y-3">
              <h3 className="text-sm font-medium text-foreground">{t('page.request_detail.actions')}</h3>

              {/* Approval actions */}
              {isPendingApproval && (
                <>
                  <button
                    onClick={() => approveRequest.mutate()}
                    disabled={approveRequest.isPending}
                    className="w-full inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-success text-white shadow-xs hover:bg-success/90 disabled:opacity-50"
                  >
                    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><path d="m9 11 3 3L22 4" /></svg>
                    {t('page.request_detail.approve')}
                  </button>
                  {!showRejectForm ? (
                    <button
                      onClick={() => setShowRejectForm(true)}
                      className="w-full inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-destructive/10 hover:text-destructive transition-all"
                    >
                      {t('page.request_detail.reject')}
                    </button>
                  ) : (
                    <div className="space-y-2">
                      <input
                        value={rejectReason}
                        onChange={(e) => setRejectReason(e.target.value)}
                        placeholder={t('page.request_detail.reject_reason_placeholder')}
                        className="w-full"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => rejectRequest.mutate()}
                          disabled={!rejectReason.trim() || rejectRequest.isPending}
                          className="flex-1 inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50"
                        >
                          {t('page.request_detail.reject')}
                        </button>
                        <button
                          onClick={() => { setShowRejectForm(false); setRejectReason(''); }}
                          className="inline-flex items-center justify-center rounded-md h-9 px-3 text-sm font-medium border bg-background shadow-xs hover:bg-accent transition-all"
                        >
                          {t('common.cancel')}
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Status transitions */}
              {nextStatuses.map((s) => (
                <button
                  key={s}
                  onClick={() => changeStatus.mutate(s)}
                  disabled={changeStatus.isPending}
                  className={`w-full inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium shadow-xs transition-all disabled:opacity-50 ${
                    s === 'resolved'
                      ? 'bg-success text-white hover:bg-success/90'
                      : s === 'rejected'
                      ? 'border bg-background hover:bg-destructive/10 hover:text-destructive'
                      : 'border bg-background hover:bg-accent hover:text-accent-foreground'
                  }`}
                >
                  {s === 'resolved' && (
                    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><path d="m9 11 3 3L22 4" /></svg>
                  )}
                  {t(`enum.${s}`, undefined, { defaultValue: humanizeToken(s) })}
                </button>
              ))}

              {/* Priority change */}
              <div>
                <label className="block text-xs text-muted-foreground mb-1">{t('table.priority')}</label>
                <select
                  value={request.priority}
                  onChange={(e) => changePriority.mutate(e.target.value)}
                  className="w-full text-sm"
                >
                  <option value="low">{t('enum.low')}</option>
                  <option value="medium">{t('enum.medium')}</option>
                  <option value="high">{t('enum.high')}</option>
                  <option value="urgent">{t('enum.urgent')}</option>
                </select>
              </div>
            </div>
          )}

          {/* AI Classification */}
          {isTech && (request.data?.ai_classification as AIClassificationData | undefined)?.ai_used === true && (
            <AIClassificationCard data={request.data.ai_classification as AIClassificationData} t={t} />
          )}

          {/* Auto Assignment */}
          {request.data?.auto_assignment != null && <AutoAssignmentCard data={request.data.auto_assignment} t={t} />}

          {/* Priority Scoring */}
          {request.data?.priority_scoring != null && isTech && (
            <div className="rounded-lg border border-border bg-card p-4 space-y-3">
              <h3 className="text-sm font-medium text-foreground">{t('page.request_detail.priority_scoring')}</h3>
              <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                {[
                  ['page.request_detail.type_weight', 'type_weight'],
                  ['page.request_detail.subtype_weight', 'subtype_weight'],
                  ['page.request_detail.department_weight', 'department_weight'],
                  ['page.request_detail.role_weight', 'role_weight'],
                  ['page.request_detail.ai_hint_weight', 'ai_hint_weight'],
                  ['page.request_detail.raw_score', 'raw_score'],
                ].map(([labelKey, fieldKey]) => {
                  const scoring = request.data.priority_scoring as Record<string, unknown>;
                  const value = scoring[fieldKey];
                  return value != null ? (
                    <div key={fieldKey} className="flex justify-between gap-2 bg-secondary rounded-lg px-2 py-1">
                      <span className="text-muted-foreground">{t(labelKey)}</span>
                      <span className="font-medium text-foreground">{String(value)}</span>
                    </div>
                  ) : null;
                })}
              </div>
            </div>
          )}

          {/* Linked POs */}
          {linkedPOs && linkedPOs.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-4 space-y-3">
              <h3 className="text-sm font-medium text-foreground">{t('page.request_detail.linked_pos')}</h3>
              <div className="space-y-2">
                {linkedPOs.map((po) => (
                  <div key={po.id} className="flex items-center justify-between bg-secondary rounded-lg px-3 py-2">
                    <div className="flex items-center gap-2">
                      <Link to={`/purchase-orders/${po.id}`} className="text-sm text-primary hover:underline font-medium">
                        {po.po_number}
                      </Link>
                      <Badge variant={po.status === 'CANCELLED' ? 'danger' : po.status === 'CLOSED' ? 'default' : 'info'}>
                        {po.status.replace('_', ' ')}
                      </Badge>
                    </div>
                    <span className="text-sm text-muted-foreground">${(po.total_amount_cents / 100).toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Shipments */}
          {isTech && linkedShipments !== undefined && (
            <div className="rounded-lg border border-border bg-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-foreground">{t('page.request_detail.shipments')}</h3>
                <Link to={`/shipments/new?request_id=${id}`} className="text-xs text-primary hover:underline">
                  {t('page.request_detail.create_shipment')}
                </Link>
              </div>
              {linkedShipments.length > 0 ? (
                <div className="space-y-2">
                  {linkedShipments.map((s) => {
                    const shipStatusColors: Record<string, string> = {
                      DRAFT: 'default', DISPATCHED: 'info', IN_TRANSIT: 'warning', DELIVERED: 'success', FAILED: 'danger', CANCELLED: 'default',
                    };
                    return (
                      <Link key={s.id} to={`/shipments/${s.id}`} className="flex items-center justify-between bg-secondary rounded-lg px-3 py-2 hover:bg-secondary/80 transition-colors">
                        <div className="flex items-center gap-2">
                          <Badge variant={shipStatusColors[s.status] || 'default'}>
                            {t(`enum.shipment_status.${s.status}`)}
                          </Badge>
                          <Badge variant={s.direction === 'outbound' ? 'info' : 'warning'}>
                            {t(`enum.shipment_direction.${s.direction}`)}
                          </Badge>
                        </div>
                        <span className="text-xs text-muted-foreground">{s.dispatched_at ? formatDateTime(s.dispatched_at) : '—'}</span>
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">{t('page.request_detail.no_shipments')}</p>
              )}
            </div>
          )}

          {/* Appointments */}
          {isTech && (
            <div className="rounded-lg border border-border bg-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-foreground">{t('page.request_detail.appointments')}</h3>
                <button
                  type="button"
                  onClick={() => {
                    if (canScheduleAppointment) setShowBooking(!showBooking);
                  }}
                  disabled={!canScheduleAppointment}
                  className={canScheduleAppointment ? 'text-xs text-primary hover:underline' : 'text-xs text-muted-foreground cursor-not-allowed'}
                >
                  {t('page.request_detail.schedule_appointment')}
                </button>
              </div>
              {!canScheduleAppointment && (
                <p className="text-xs text-muted-foreground">{appointmentScheduleHint}</p>
              )}

              {showBooking && canScheduleAppointment && request.assigned_to && (
                <div className="bg-primary/5 rounded-lg p-3 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block mb-1 text-xs text-muted-foreground">{t('page.request_detail.select_date')}</label>
                      <input
                        type="date"
                        value={bookingDate}
                        onChange={(e) => { setBookingDate(e.target.value); setBookingSlot(''); }}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block mb-1 text-xs text-muted-foreground">{t('page.request_detail.duration')}</label>
                      <select value={bookingDuration} onChange={(e) => setBookingDuration(Number(e.target.value))} className="w-full">
                        <option value={30}>30 min</option>
                        <option value={60}>60 min</option>
                        <option value={90}>90 min</option>
                      </select>
                    </div>
                  </div>

                  {bookingDate && (
                    <div>
                      <label className="block mb-1 text-xs text-muted-foreground">{t('page.request_detail.select_slot')}</label>
                      {availableSlots && availableSlots.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {availableSlots.map((slot) => {
                            const slotDateTime = buildSlotDateTime(bookingDate, slot.start);
                            const label = formatSlotLabel(slot.start);
                            return (
                              <button
                                key={slot.start}
                                onClick={() => setBookingSlot(slotDateTime)}
                                className={`px-2 py-1 rounded text-xs border ${bookingSlot === slotDateTime ? 'bg-primary text-white border-primary' : 'bg-card hover:bg-secondary'}`}
                              >
                                {label}
                              </button>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">{t('page.request_detail.no_slots')}</p>
                      )}
                    </div>
                  )}

                  <div>
                    <label className="block mb-1 text-xs text-muted-foreground">{t('page.request_detail.location')}</label>
                    <input value={bookingLocation} onChange={(e) => setBookingLocation(e.target.value)} className="w-full" />
                  </div>

                  <button
                    onClick={() => scheduleAppointment.mutate()}
                    disabled={!bookingSlot || scheduleAppointment.isPending}
                    className="w-full inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                  >
                    {t('page.request_detail.schedule_appointment')}
                  </button>
                </div>
              )}

              {appointmentsList && appointmentsList.length > 0 ? (
                <div className="space-y-2">
                  {appointmentsList.map((a) => {
                    const statusColorMap: Record<string, string> = {
                      PENDING: 'warning', CONFIRMED: 'info', COMPLETED: 'success', CANCELLED: 'danger', NO_SHOW: 'default',
                    };
                    return (
                      <div key={a.id} className="flex items-center justify-between bg-secondary rounded-lg px-3 py-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-foreground">{formatDateTime(a.scheduled_start)}</span>
                          <span className="text-xs text-muted-foreground">{a.duration_minutes}m</span>
                        </div>
                        <Badge variant={statusColorMap[a.status] || 'default'}>
                          {t(`enum.appointment_status.${a.status}`)}
                        </Badge>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">{t('page.request_detail.no_appointments')}</p>
              )}
            </div>
          )}

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
