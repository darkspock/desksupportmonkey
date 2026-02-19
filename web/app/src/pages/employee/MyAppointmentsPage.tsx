import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { useToast } from '../../hooks/useToast';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { Appointment, PaginatedResponse } from '../../types';

const statusColors: Record<string, string> = {
  PENDING: 'warning',
  CONFIRMED: 'info',
  COMPLETED: 'success',
  CANCELLED: 'danger',
  NO_SHOW: 'default',
};

export default function MyAppointmentsPage() {
  const [page, setPage] = useState(1);
  const [cancelId, setCancelId] = useState<string | null>(null);
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['my-appointments', page],
    queryFn: async () => {
      const { data } = await api.get('/my/appointments', { params: { page, page_size: 20 } });
      return data as PaginatedResponse<Appointment>;
    },
  });

  const cancelAppointment = useMutation({
    mutationFn: async (appointmentId: string) => {
      await api.post(`/appointments/${appointmentId}/cancel`, {
        reason: 'Cancelled by employee',
      });
    },
    onSuccess: () => {
      setCancelId(null);
      queryClient.invalidateQueries({ queryKey: ['my-appointments'] });
      showToast({ title: t('page.my_appointments.toast_cancelled'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error';
      showToast({ title: detail, variant: 'error' });
    },
  });

  const upcoming = data?.data.filter((a) => a.status === 'PENDING' || a.status === 'CONFIRMED') ?? [];
  const past = data?.data.filter((a) => a.status !== 'PENDING' && a.status !== 'CONFIRMED') ?? [];

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.my_appointments.title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.my_appointments.subtitle')}</p>
      </div>

      <Card>
        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => { void refetch(); }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.my_appointments.no_appointments')} />
        ) : (
          <>
            {upcoming.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-foreground mb-3">{t('page.my_appointments.upcoming')}</h3>
                <div className="space-y-2">
                  {upcoming.map((a) => (
                    <div key={a.id} className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3">
                      <div className="flex items-center gap-4">
                        <div>
                          <p className="text-sm font-medium text-foreground">{formatDateTime(a.scheduled_start)}</p>
                          <p className="text-xs text-muted-foreground">{a.duration_minutes} min</p>
                        </div>
                        <div>
                          <p className="text-sm text-foreground">{a.technician_email || a.technician_id}</p>
                          {a.location && <p className="text-xs text-muted-foreground">{a.location}</p>}
                        </div>
                        <Badge variant={statusColors[a.status] || 'default'}>
                          {t(`enum.appointment_status.${a.status}`)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/requests/${a.request_id}`}
                          className="text-xs text-primary hover:underline"
                        >
                          {t('page.request_detail.appointments')}
                        </Link>
                        {(a.status === 'PENDING' || a.status === 'CONFIRMED') && (
                          <button
                            onClick={() => setCancelId(a.id)}
                            className="text-xs text-destructive hover:underline"
                          >
                            {t('common.cancel')}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {past.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3">{t('page.my_appointments.past')}</h3>
                <div className="space-y-2">
                  {past.map((a) => (
                    <div key={a.id} className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
                      <div className="flex items-center gap-4">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">{formatDateTime(a.scheduled_start)}</p>
                          <p className="text-xs text-muted-foreground">{a.duration_minutes} min</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">{a.technician_email || a.technician_id}</p>
                        </div>
                        <Badge variant={statusColors[a.status] || 'default'}>
                          {t(`enum.appointment_status.${a.status}`)}
                        </Badge>
                      </div>
                      <Link
                        to={`/requests/${a.request_id}`}
                        className="text-xs text-primary hover:underline"
                      >
                        {t('page.request_detail.appointments')}
                      </Link>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </>
        )}
      </Card>

      <ConfirmDialog
        open={cancelId !== null}
        title={t('page.my_appointments.cancel')}
        description={t('page.my_appointments.cancel_confirm')}
        onConfirm={() => { if (cancelId) cancelAppointment.mutate(cancelId); }}
        onCancel={() => setCancelId(null)}
        tone="danger"
      />
    </div>
  );
}
