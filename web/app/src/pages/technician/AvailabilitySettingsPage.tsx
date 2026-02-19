import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { Card } from '../../components/ui/Card';
import { useToast } from '../../hooks/useToast';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { AvailabilityWindow, AvailabilityOverrideItem } from '../../types';

interface WindowForm {
  day_of_week: number;
  enabled: boolean;
  start_time: string;
  end_time: string;
}

const DEFAULT_WINDOWS: WindowForm[] = Array.from({ length: 7 }, (_, i) => ({
  day_of_week: i,
  enabled: i < 5, // Mon-Fri enabled by default
  start_time: '09:00',
  end_time: '17:00',
}));

const DAY_KEYS = ['day.0', 'day.1', 'day.2', 'day.3', 'day.4', 'day.5', 'day.6'];

export default function AvailabilitySettingsPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const techId = user?.id ?? '';

  const [windows, setWindows] = useState<WindowForm[]>(DEFAULT_WINDOWS);
  const [overrideDate, setOverrideDate] = useState('');
  const [overrideAvailable, setOverrideAvailable] = useState(false);
  const [overrideStart, setOverrideStart] = useState('09:00');
  const [overrideEnd, setOverrideEnd] = useState('17:00');
  const [overrideReason, setOverrideReason] = useState('');

  const { data: existingWindows, isLoading: loadingWindows, isError: errorWindows, error: windowsError, refetch: refetchWindows } = useQuery({
    queryKey: ['availability', techId],
    queryFn: async () => {
      const { data } = await api.get(`/availability/technicians/${techId}`);
      return data.data as AvailabilityWindow[];
    },
    enabled: !!techId,
  });

  useEffect(() => {
    if (existingWindows) {
      const updated = DEFAULT_WINDOWS.map((w) => {
        const existing = existingWindows.find((e) => e.day_of_week === w.day_of_week);
        if (existing) {
          return { ...w, enabled: true, start_time: existing.start_time, end_time: existing.end_time };
        }
        return { ...w, enabled: false };
      });
      setWindows(updated);
    }
  }, [existingWindows]);

  // Overrides — show next 60 days
  const now = new Date();
  const sixtyDaysLater = new Date(now);
  sixtyDaysLater.setDate(sixtyDaysLater.getDate() + 60);
  const dateFrom = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  const dateTo = `${sixtyDaysLater.getFullYear()}-${String(sixtyDaysLater.getMonth() + 1).padStart(2, '0')}-${String(sixtyDaysLater.getDate()).padStart(2, '0')}`;

  const { data: overrides, isLoading: loadingOverrides } = useQuery({
    queryKey: ['availability-overrides', techId, dateFrom, dateTo],
    queryFn: async () => {
      const { data } = await api.get(`/availability/technicians/${techId}/overrides`, {
        params: { date_from: dateFrom, date_to: dateTo },
      });
      return data.data as AvailabilityOverrideItem[];
    },
    enabled: !!techId,
  });

  const saveSchedule = useMutation({
    mutationFn: async () => {
      const payload = windows
        .filter((w) => w.enabled)
        .map((w) => ({ day_of_week: w.day_of_week, start_time: w.start_time, end_time: w.end_time }));
      await api.put(`/availability/technicians/${techId}`, { windows: payload });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['availability', techId] });
      showToast({ title: t('page.availability.toast_saved'), variant: 'success' });
    },
    onError: () => {
      showToast({ title: t('page.availability.error'), variant: 'error' });
    },
  });

  const addOverride = useMutation({
    mutationFn: async () => {
      await api.post(`/availability/technicians/${techId}/overrides`, {
        date: overrideDate,
        is_available: overrideAvailable,
        start_time: overrideAvailable ? overrideStart : null,
        end_time: overrideAvailable ? overrideEnd : null,
        reason: overrideReason || null,
      });
    },
    onSuccess: () => {
      setOverrideDate('');
      setOverrideReason('');
      queryClient.invalidateQueries({ queryKey: ['availability-overrides', techId] });
      showToast({ title: t('page.availability.toast_override_added'), variant: 'success' });
    },
    onError: () => {
      showToast({ title: t('page.availability.error'), variant: 'error' });
    },
  });

  const deleteOverride = useMutation({
    mutationFn: async (overrideId: string) => {
      await api.delete(`/availability/overrides/${overrideId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['availability-overrides', techId] });
      showToast({ title: t('page.availability.toast_override_deleted'), variant: 'success' });
    },
    onError: () => {
      showToast({ title: t('page.availability.error'), variant: 'error' });
    },
  });

  if (loadingWindows) return <Loading />;
  if (errorWindows) {
    return (
      <ErrorState
        message={(windowsError as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
        onRetry={() => { void refetchWindows(); }}
      />
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.availability.title')}</h2>

      {/* Recurring Schedule */}
      <Card>
        <h3 className="text-sm font-semibold text-foreground mb-4">{t('page.availability.recurring')}</h3>
        <div className="space-y-3">
          {windows.map((w, i) => (
            <div key={w.day_of_week} className="flex items-center gap-3">
              <label className="flex items-center gap-2 w-32">
                <input
                  type="checkbox"
                  checked={w.enabled}
                  onChange={(e) => {
                    const updated = [...windows];
                    updated[i] = { ...updated[i], enabled: e.target.checked };
                    setWindows(updated);
                  }}
                  className="rounded"
                />
                <span className="text-sm text-foreground">{t(DAY_KEYS[w.day_of_week])}</span>
              </label>
              {w.enabled && (
                <>
                  <input
                    type="time"
                    value={w.start_time}
                    onChange={(e) => {
                      const updated = [...windows];
                      updated[i] = { ...updated[i], start_time: e.target.value };
                      setWindows(updated);
                    }}
                    className="text-sm"
                  />
                  <span className="text-muted-foreground">—</span>
                  <input
                    type="time"
                    value={w.end_time}
                    onChange={(e) => {
                      const updated = [...windows];
                      updated[i] = { ...updated[i], end_time: e.target.value };
                      setWindows(updated);
                    }}
                    className="text-sm"
                  />
                </>
              )}
            </div>
          ))}
        </div>
        <button
          onClick={() => saveSchedule.mutate()}
          disabled={saveSchedule.isPending}
          className="mt-4 inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {saveSchedule.isPending ? t('common.working') : t('common.save')}
        </button>
      </Card>

      {/* Overrides */}
      <Card>
        <h3 className="text-sm font-semibold text-foreground mb-4">{t('page.availability.overrides')}</h3>

        {/* Add override form */}
        <div className="bg-secondary rounded-lg p-3 mb-4 space-y-3">
          <h4 className="text-xs font-medium text-muted-foreground">{t('page.availability.add_override')}</h4>
          <div className="flex items-center gap-3 flex-wrap">
            <input
              type="date"
              value={overrideDate}
              onChange={(e) => setOverrideDate(e.target.value)}
              className="text-sm"
            />
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={overrideAvailable}
                onChange={(e) => setOverrideAvailable(e.target.checked)}
                className="rounded"
              />
              {t('page.availability.extra_hours')}
            </label>
            {overrideAvailable && (
              <>
                <input
                  type="time"
                  value={overrideStart}
                  onChange={(e) => setOverrideStart(e.target.value)}
                  className="text-sm"
                />
                <span className="text-muted-foreground">—</span>
                <input
                  type="time"
                  value={overrideEnd}
                  onChange={(e) => setOverrideEnd(e.target.value)}
                  className="text-sm"
                />
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            <input
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder={t('page.availability.reason')}
              className="flex-1 text-sm"
            />
            <button
              onClick={() => addOverride.mutate()}
              disabled={!overrideDate || addOverride.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {t('common.save')}
            </button>
          </div>
        </div>

        {/* Override list */}
        {loadingOverrides ? (
          <Loading />
        ) : !overrides?.length ? (
          <p className="text-sm text-muted-foreground">{t('page.availability.no_overrides')}</p>
        ) : (
          <div className="space-y-2">
            {overrides.map((o) => (
              <div key={o.id} className="flex items-center justify-between bg-secondary rounded-lg px-3 py-2">
                <div>
                  <span className="text-sm font-medium text-foreground">{formatDate(o.date)}</span>
                  {o.is_available ? (
                    <span className="ml-2 text-xs text-success">{o.start_time} — {o.end_time}</span>
                  ) : (
                    <span className="ml-2 text-xs text-destructive">{t('page.availability.block_day')}</span>
                  )}
                  {o.reason && <span className="ml-2 text-xs text-muted-foreground">({o.reason})</span>}
                </div>
                <button
                  onClick={() => deleteOverride.mutate(o.id)}
                  className="rounded-md px-2 py-1 text-sm text-destructive hover:bg-accent hover:text-accent-foreground transition-colors"
                >
                  {t('common.delete')}
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
