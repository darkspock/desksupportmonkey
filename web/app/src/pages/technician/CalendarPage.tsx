import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { useI18n } from '../../lib/i18n';
import type { Appointment, MaintenanceRecord } from '../../types';

function getMonday(d: Date): Date {
  const date = new Date(d);
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + diff);
  date.setHours(0, 0, 0, 0);
  return date;
}

function formatDateISO(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${dd}`;
}

function formatDateShort(d: Date): string {
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

const HOURS = Array.from({ length: 11 }, (_, i) => i + 8); // 8:00-18:00
const DAY_NAMES = ['day.0', 'day.1', 'day.2', 'day.3', 'day.4', 'day.5', 'day.6'];

const statusColors: Record<string, string> = {
  PENDING: 'warning',
  CONFIRMED: 'info',
  COMPLETED: 'success',
  CANCELLED: 'danger',
  NO_SHOW: 'default',
  SCHEDULED: 'info',
  IN_PROGRESS: 'warning',
  SKIPPED: 'default',
};

type CalendarEvent = {
  id: string;
  kind: 'appointment' | 'maintenance';
  start: string;
  status: string;
  title: string;
  subtitle: string;
  link: string;
};

export default function CalendarPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [weekStart, setWeekStart] = useState(() => getMonday(new Date()));

  const weekDates = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(weekStart);
      d.setDate(d.getDate() + i);
      return d;
    });
  }, [weekStart]);

  const dateFrom = formatDateISO(weekDates[0]);
  const dateTo = formatDateISO(weekDates[6]);

  const { data: events, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['calendar-events', user?.id, dateFrom, dateTo],
    queryFn: async () => {
      const appointmentParams: Record<string, string> = {
        page: '1',
        page_size: '100',
        date_from: `${dateFrom}T00:00:00`,
        date_to: `${dateTo}T23:59:59`,
      };
      const maintenanceParams: Record<string, string> = {
        page: '1',
        page_size: '100',
        scheduled_from: `${dateFrom}T00:00:00`,
        scheduled_to: `${dateTo}T23:59:59`,
      };
      const [appointmentsResponse, maintenanceResponse] = await Promise.all([
        api.get('/appointments', { params: appointmentParams }),
        api.get('/maintenance', { params: maintenanceParams }),
      ]);

      const weekStartBoundary = weekDates[0];
      const weekEndBoundary = new Date(weekDates[6].getTime() + 86400000);

      const appointmentEvents = (appointmentsResponse.data.data as Appointment[]).map((a) => ({
        id: a.id,
        kind: 'appointment' as const,
        start: a.scheduled_start,
        status: a.status,
        title: t('page.calendar.type_appointment'),
        subtitle: a.employee_email || a.employee_id,
        link: `/requests/${a.request_id}`,
      }));
      const maintenanceEvents = (maintenanceResponse.data.data as MaintenanceRecord[])
        .filter((m) => !!m.scheduled_at)
        .map((m) => ({
          id: m.id,
          kind: 'maintenance' as const,
          start: m.scheduled_at as string,
          status: m.status,
          title: t('page.calendar.type_maintenance'),
          subtitle: m.title,
          link: `/maintenance/${m.id}`,
        }));

      return [...appointmentEvents, ...maintenanceEvents].filter((event) => {
        const start = new Date(event.start);
        return start >= weekStartBoundary && start <= weekEndBoundary;
      });
    },
    enabled: !!user?.id,
  });

  const prevWeek = () => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() - 7);
    setWeekStart(d);
  };

  const nextWeek = () => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + 7);
    setWeekStart(d);
  };

  const goToday = () => setWeekStart(getMonday(new Date()));

  // Group events by day-of-week index (0=Mon, 6=Sun)
  const byDay = useMemo(() => {
    const map: Record<number, CalendarEvent[]> = {};
    for (let i = 0; i < 7; i++) map[i] = [];
    if (events) {
      for (const event of events) {
        const start = new Date(event.start);
        const dayIdx = (start.getDay() + 6) % 7; // Mon=0
        if (map[dayIdx]) map[dayIdx].push(event);
      }
    }
    return map;
  }, [events]);

  const weekStats = useMemo(() => {
    const all = events ?? [];
    return {
      total: all.length,
      appointments: all.filter(e => e.kind === 'appointment').length,
      maintenance: all.filter(e => e.kind === 'maintenance').length,
      completed: all.filter(e => e.status === 'COMPLETED').length,
      cancelled: all.filter(e => e.status === 'CANCELLED').length,
    };
  }, [events]);

  const statItems = [
    {
      label: t('page.calendar.stat_total'),
      value: weekStats.total,
      colorClass: 'text-primary',
      bgClass: 'bg-primary/10',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="4" width="18" height="18" rx="2" />
          <path d="M16 2v4M8 2v4M3 10h18" />
        </svg>
      ),
    },
    {
      label: t('page.calendar.stat_appointments'),
      value: weekStats.appointments,
      colorClass: 'text-primary',
      bgClass: 'bg-primary/10',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 6v6l4 2" />
        </svg>
      ),
    },
    {
      label: t('page.calendar.stat_maintenance'),
      value: weekStats.maintenance,
      colorClass: 'text-warning-foreground',
      bgClass: 'bg-warning/15',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76Z" />
        </svg>
      ),
    },
    {
      label: t('page.calendar.stat_completed'),
      value: weekStats.completed,
      colorClass: 'text-success',
      bgClass: 'bg-success/15',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <path d="m9 11 3 3L22 4" />
        </svg>
      ),
    },
    {
      label: t('page.calendar.stat_cancelled'),
      value: weekStats.cancelled,
      colorClass: 'text-muted-foreground',
      bgClass: 'bg-muted',
      icon: (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="m15 9-6 6M9 9l6 6" />
        </svg>
      ),
    },
  ];

  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <ErrorState
        message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
        onRetry={() => { void refetch(); }}
      />
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.calendar.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.calendar.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={prevWeek} className="inline-flex h-9 w-9 items-center justify-center rounded-md border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 18-6-6 6-6" /></svg>
          </button>
          <button onClick={goToday} className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all">{t('page.calendar.today')}</button>
          <button onClick={nextWeek} className="inline-flex h-9 w-9 items-center justify-center rounded-md border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 18 6-6-6-6" /></svg>
          </button>
        </div>
      </div>

      {/* Weekly stats */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-2">
          {t('page.calendar.this_week')} · {formatDateShort(weekDates[0])} – {formatDateShort(weekDates[6])}
        </p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {statItems.map((stat) => (
            <div
              key={stat.label}
              className="flex items-center gap-3 rounded-lg border border-border bg-card p-3.5"
            >
              <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${stat.bgClass}`}>
                <span className={stat.colorClass}>{stat.icon}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-semibold leading-none text-foreground">{stat.value}</span>
                <span className="mt-1 text-xs text-muted-foreground">{stat.label}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Calendar grid */}
      <Card>
        <div className="overflow-x-auto">
          <div className="min-w-[700px]">
            {/* Header row */}
            <div className="grid grid-cols-8 border-b">
              <div className="p-2 text-xs text-muted-foreground"></div>
              {weekDates.map((d, i) => {
                const isToday = formatDateISO(d) === formatDateISO(new Date());
                return (
                  <div key={i} className={`p-2 text-center text-xs font-medium ${isToday ? 'bg-primary/10 text-primary' : 'text-muted-foreground'}`}>
                    <div>{t(DAY_NAMES[i])}</div>
                    <div className="text-lg font-bold">{d.getDate()}</div>
                  </div>
                );
              })}
            </div>

            {/* Time rows */}
            {HOURS.map((hour) => (
              <div key={hour} className="grid grid-cols-8 border-b last:border-b-0 min-h-[60px]">
                <div className="p-1 text-xs text-muted-foreground text-right pr-2 pt-1">
                  {String(hour).padStart(2, '0')}:00
                </div>
                {weekDates.map((_, dayIdx) => {
                  const dayEvents = byDay[dayIdx]?.filter((event) => {
                    const h = new Date(event.start).getHours();
                    return h === hour;
                  }) ?? [];

                  return (
                    <div key={dayIdx} className="border-l p-0.5 min-h-[60px]">
                      {dayEvents.map((event) => {
                        const start = new Date(event.start);
                        const timeStr = `${String(start.getHours()).padStart(2, '0')}:${String(start.getMinutes()).padStart(2, '0')}`;
                        const bgClass = event.kind === 'appointment'
                          ? 'bg-primary/10 border-primary/20 hover:bg-primary/10'
                          : 'bg-warning/10 border-warning/20 hover:bg-warning/10';
                        const statusLabel = event.kind === 'appointment'
                          ? t(`enum.appointment_status.${event.status}`)
                          : t(`enum.maintenance_status.${event.status.toLowerCase()}`);
                        return (
                          <Link
                            key={`${event.kind}-${event.id}`}
                            to={event.link}
                            className={`block border rounded p-1 mb-0.5 transition-colors ${bgClass}`}
                          >
                            <div className="text-[10px] text-foreground font-medium">{timeStr} · {event.title}</div>
                            <div className="text-[10px] text-foreground truncate">{event.subtitle}</div>
                            <Badge variant={statusColors[event.status] || 'default'}>
                              {statusLabel}
                            </Badge>
                          </Link>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        {(!events || events.length === 0) && (
          <p className="text-center text-sm text-muted-foreground py-4">{t('page.calendar.no_events')}</p>
        )}
      </Card>
    </div>
  );
}
