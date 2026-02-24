import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Pagination } from '../../components/ui/Pagination';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { CustomFieldFilters } from '../../components/custom-fields/CustomFieldFilters';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { IncidentListItem, PaginatedResponse } from '../../types';

const severityVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  P1: 'danger',
  P2: 'warning',
  P3: 'info',
  P4: 'default',
};

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger' | 'purple'> = {
  detected: 'danger',
  triaged: 'warning',
  contained: 'info',
  eradicated: 'purple',
  recovered: 'success',
  closed: 'default',
};

export default function IncidentsList() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [severity, setSeverity] = useState('');
  const [incidentType, setIncidentType] = useState('');
  const [search, setSearch] = useState('');
  const [cfFilters, setCfFilters] = useState<Record<string, string>>({});

  const handleCfFilterChange = (key: string, value: string) => {
    setCfFilters((prev) => {
      const next = { ...prev };
      if (value) { next[key] = value; } else { delete next[key]; }
      return next;
    });
    setPage(1);
  };

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['incidents', page, status, severity, incidentType, search, cfFilters],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: 20 };
      if (status) params.status = status;
      if (severity) params.severity = severity;
      if (incidentType) params.incident_type = incidentType;
      if (search.trim()) params.search = search.trim();
      Object.entries(cfFilters).forEach(([k, v]) => { if (v) params[k] = v; });
      const { data } = await api.get('/incidents', { params });
      return data as PaginatedResponse<IncidentListItem>;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.incidents.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.incidents.subtitle')}</p>
        </div>
        <Link
          to="/incidents/new"
          className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.incidents.new')}
        </Link>
      </div>

      <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
          <input
            type="search"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder={t('page.incidents.search_placeholder')}
            className="w-full"
          />
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="w-full"
          >
            <option value="">{t('page.incidents.all_statuses')}</option>
            {['detected', 'triaged', 'contained', 'eradicated', 'recovered', 'closed'].map((s) => (
              <option key={s} value={s}>{t(`enum.incident_status.${s}`)}</option>
            ))}
          </select>
          <select
            value={severity}
            onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
            className="w-full"
          >
            <option value="">{t('page.incidents.all_severities')}</option>
            {['P1', 'P2', 'P3', 'P4'].map((s) => (
              <option key={s} value={s}>{t(`enum.incident_severity.${s}`)}</option>
            ))}
          </select>
          <select
            value={incidentType}
            onChange={(e) => { setIncidentType(e.target.value); setPage(1); }}
            className="w-full"
          >
            <option value="">{t('page.incidents.all_types')}</option>
            {['phishing', 'malware', 'ransomware', 'data_breach', 'unauthorized_access', 'ddos', 'social_engineering', 'insider_threat', 'other'].map((t_) => (
              <option key={t_} value={t_}>{t(`enum.incident_type.${t_}`)}</option>
            ))}
          </select>
        </div>
      </div>
      <CustomFieldFilters entityType="incident" filters={cfFilters} onFilterChange={handleCfFilterChange} />

      {isLoading ? <Loading /> : isError ? (
        <ErrorState
          message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
          onRetry={() => { void refetch(); }}
        />
      ) : !data?.data.length ? (
        <EmptyState message={t('page.incidents.empty')} />
      ) : (
        <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/40">
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.severity')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.status')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.title')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.type')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.assigned_to')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.detected_at')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((r) => (
                  <tr key={r.id} className="border-b border-border/80 hover:bg-accent/30">
                    <td className="px-4 py-3 align-top">
                      <Badge variant={severityVariant[r.severity] || 'default'}>
                        {t(`enum.incident_severity.${r.severity}`)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 align-top">
                      <Badge variant={statusVariant[r.status] || 'default'}>
                        {t(`enum.incident_status.${r.status}`)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 align-top text-foreground">{r.title}</td>
                    <td className="px-4 py-3 align-top text-foreground">{t(`enum.incident_type.${r.incident_type}`)}</td>
                    <td className="px-4 py-3 align-top text-foreground">{r.assigned_to_name || t('common.unassigned')}</td>
                    <td className="px-4 py-3 align-top text-muted-foreground">{r.detected_at ? formatDateTime(r.detected_at) : '—'}</td>
                    <td className="px-4 py-3 align-top">
                      <Link
                        to={`/incidents/${r.id}`}
                        className="inline-flex h-8 items-center rounded-md border border-border px-3 text-xs font-medium text-foreground hover:bg-accent"
                      >
                        {t('table.details')}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-border bg-card px-4 py-3">
            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </div>
        </div>
      )}
    </div>
  );
}
