import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Pagination } from '../../components/ui/Pagination';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../hooks/useToast';
import type { Vulnerability, PaginatedResponse } from '../../types';

const severityVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  critical: 'danger',
  high: 'warning',
  medium: 'info',
  low: 'success',
  info: 'default',
};

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger' | 'purple'> = {
  new: 'default',
  analyzing: 'info',
  confirmed: 'warning',
  false_positive: 'default',
  accepted: 'purple',
  remediation_in_progress: 'info',
  remediated: 'success',
  closed: 'default',
};

interface FormValues {
  title: string;
  cve_id: string;
  description: string;
  cvss_score: string;
  severity: string;
  affected_software: string;
  affected_versions: string;
  remediation_notes: string;
}

const EMPTY_FORM: FormValues = {
  title: '',
  cve_id: '',
  description: '',
  cvss_score: '',
  severity: '',
  affected_software: '',
  affected_versions: '',
  remediation_notes: '',
};

export default function VulnerabilitiesPage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formValues, setFormValues] = useState<FormValues>(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const [showImport, setShowImport] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<{
    total: number; successful: number; skipped: number;
    failed: { row: number; error: string }[];
  } | null>(null);
  const pageSize = 20;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['vulnerabilities', page, search, severity, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', String(pageSize));
      if (search) params.set('search', search);
      if (severity) params.set('severity', severity);
      if (statusFilter) params.set('status', statusFilter);
      const { data } = await api.get(`/vulnerabilities?${params}`);
      return data as PaginatedResponse<Vulnerability>;
    },
  });

  const create = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        title: formValues.title.trim(),
      };
      if (formValues.cve_id.trim()) payload.cve_id = formValues.cve_id.trim();
      if (formValues.description.trim()) payload.description = formValues.description.trim();
      if (formValues.cvss_score) payload.cvss_score = parseFloat(formValues.cvss_score);
      if (formValues.severity && !formValues.cvss_score) payload.severity = formValues.severity;
      if (formValues.affected_software.trim()) payload.affected_software = formValues.affected_software.trim();
      if (formValues.affected_versions.trim()) payload.affected_versions = formValues.affected_versions.trim();
      if (formValues.remediation_notes.trim()) payload.remediation_notes = formValues.remediation_notes.trim();
      await api.post('/vulnerabilities', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vulnerabilities'] });
      setShowForm(false);
      setFormValues(EMPTY_FORM);
      setFormError('');
      showToast({ title: t('page.vulnerabilities.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error creating vulnerability';
      setFormError(detail);
      showToast({ title: t('page.vulnerabilities.error_create'), description: detail, variant: 'error' });
    },
  });

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/vulnerabilities/import', formData);
      return data.data as { total: number; successful: number; skipped: number; failed: { row: number; error: string }[] };
    },
    onSuccess: (result) => {
      setImportResult(result);
      if (result.successful > 0) {
        queryClient.invalidateQueries({ queryKey: ['vulnerabilities'] });
        showToast({ title: t('page.vulnerabilities.toast_imported', { count: String(result.successful) }), variant: 'success' });
      }
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Import failed';
      showToast({ title: t('page.vulnerabilities.error_import'), description: detail, variant: 'error' });
    },
  });

  const handleImport = () => {
    if (!importFile) return;
    setImportResult(null);
    importMutation.mutate(importFile);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formValues.title.trim()) {
      setFormError('Title is required');
      return;
    }
    if (!formValues.cvss_score && !formValues.severity) {
      setFormError('Either CVSS score or severity is required');
      return;
    }
    setFormError('');
    create.mutate();
  };

  const selectClasses = 'h-9 rounded-md border border-border bg-card px-3 text-sm text-foreground';
  const inputClasses = 'w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring';

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.vulnerabilities.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.vulnerabilities.subtitle')}</p>
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            <button
              onClick={() => { setShowImport(true); setImportFile(null); setImportResult(null); }}
              className="inline-flex h-9 items-center justify-center rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50"
            >
              {t('page.vulnerabilities.import')}
            </button>
            <button
              onClick={() => { setShowForm(true); setFormValues(EMPTY_FORM); setFormError(''); }}
              className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
            >
              {t('page.vulnerabilities.add')}
            </button>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder={t('page.vulnerabilities.search_placeholder')}
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className={`${selectClasses} w-64`}
        />
        <select value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1); }} className={selectClasses}>
          <option value="">{t('page.vulnerabilities.filter_severity')}</option>
          <option value="critical">{t('enum.vuln_severity.critical')}</option>
          <option value="high">{t('enum.vuln_severity.high')}</option>
          <option value="medium">{t('enum.vuln_severity.medium')}</option>
          <option value="low">{t('enum.vuln_severity.low')}</option>
          <option value="info">{t('enum.vuln_severity.info')}</option>
        </select>
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className={selectClasses}>
          <option value="">{t('page.vulnerabilities.filter_status')}</option>
          <option value="new">{t('enum.vuln_status.new')}</option>
          <option value="analyzing">{t('enum.vuln_status.analyzing')}</option>
          <option value="confirmed">{t('enum.vuln_status.confirmed')}</option>
          <option value="false_positive">{t('enum.vuln_status.false_positive')}</option>
          <option value="accepted">{t('enum.vuln_status.accepted')}</option>
          <option value="remediation_in_progress">{t('enum.vuln_status.remediation_in_progress')}</option>
          <option value="remediated">{t('enum.vuln_status.remediated')}</option>
          <option value="closed">{t('enum.vuln_status.closed')}</option>
        </select>
      </div>

      {isLoading && <Loading />}
      {isError && <ErrorState message={(error as Error).message} onRetry={refetch} />}

      {data && data.data.length === 0 && (
        <EmptyState message={t('page.vulnerabilities.no_results')} />
      )}

      {data && data.data.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  <th className="px-4 py-3">{t('page.vulnerabilities.col_cve_id')}</th>
                  <th className="px-4 py-3">{t('page.vulnerabilities.col_title')}</th>
                  <th className="px-4 py-3">{t('page.vulnerabilities.col_severity')}</th>
                  <th className="px-4 py-3">{t('page.vulnerabilities.col_status')}</th>
                  <th className="px-4 py-3">{t('page.vulnerabilities.col_software')}</th>
                  <th className="px-4 py-3">{t('page.vulnerabilities.col_cvss')}</th>
                  <th className="px-4 py-3">{t('page.vulnerabilities.col_created')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.data.map((v) => (
                  <tr key={v.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">
                      {v.cve_id || '—'}
                    </td>
                    <td className="px-4 py-3 font-medium">
                      <Link to={`/vulnerabilities/${v.id}`} className="text-primary hover:underline">
                        {v.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={severityVariant[v.severity] || 'default'}>
                        {t(`enum.vuln_severity.${v.severity}`)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusVariant[v.status] || 'default'}>
                        {t(`enum.vuln_status.${v.status}`)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {v.affected_software || '—'}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {v.cvss_score != null ? v.cvss_score.toFixed(1) : '—'}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {v.created_at ? formatDateTime(v.created_at) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={data.meta.page}
            pageSize={data.meta.page_size}
            total={data.meta.total}
            onChange={setPage}
          />
        </>
      )}

      {/* Import Modal */}
      {showImport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-2 text-lg font-semibold text-foreground">{t('page.vulnerabilities.import_title')}</h3>
            <p className="mb-4 text-sm text-muted-foreground">{t('page.vulnerabilities.import_description')}</p>

            {!importResult && (
              <div className="flex flex-col gap-3">
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  className="text-sm text-foreground file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-primary-foreground hover:file:bg-primary/90"
                />
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowImport(false)}
                    className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50"
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    type="button"
                    disabled={!importFile || importMutation.isPending}
                    onClick={handleImport}
                    className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
                  >
                    {importMutation.isPending ? t('page.vulnerabilities.import_uploading') : t('page.vulnerabilities.import')}
                  </button>
                </div>
              </div>
            )}

            {importResult && (
              <div className="flex flex-col gap-3">
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div className="rounded-md bg-muted/50 p-3 text-center">
                    <div className="text-lg font-semibold text-foreground">{importResult.total}</div>
                    <div className="text-muted-foreground">{t('page.vulnerabilities.import_total')}</div>
                  </div>
                  <div className="rounded-md bg-green-500/10 p-3 text-center">
                    <div className="text-lg font-semibold text-green-600">{importResult.successful}</div>
                    <div className="text-muted-foreground">{t('page.vulnerabilities.import_successful')}</div>
                  </div>
                  <div className="rounded-md bg-yellow-500/10 p-3 text-center">
                    <div className="text-lg font-semibold text-yellow-600">{importResult.skipped}</div>
                    <div className="text-muted-foreground">{t('page.vulnerabilities.import_skipped')}</div>
                  </div>
                </div>
                {importResult.failed.length > 0 && (
                  <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3">
                    <p className="mb-2 text-sm font-medium text-destructive">{t('page.vulnerabilities.import_failed')} ({importResult.failed.length})</p>
                    <ul className="space-y-1 text-xs text-destructive">
                      {importResult.failed.map((f) => (
                        <li key={f.row}>{t('page.vulnerabilities.import_error_row', { row: String(f.row) })}: {f.error}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => setShowImport(false)}
                    className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90"
                  >
                    {t('common.close')}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold text-foreground">{t('page.vulnerabilities.add')}</h3>
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <input
                placeholder={t('page.vulnerabilities.field_title') + ' *'}
                value={formValues.title}
                onChange={(e) => setFormValues({ ...formValues, title: e.target.value })}
                className={inputClasses}
              />
              <input
                placeholder={t('page.vulnerabilities.field_cve_id')}
                value={formValues.cve_id}
                onChange={(e) => setFormValues({ ...formValues, cve_id: e.target.value })}
                className={inputClasses}
              />
              <textarea
                placeholder={t('page.vulnerabilities.field_description')}
                value={formValues.description}
                onChange={(e) => setFormValues({ ...formValues, description: e.target.value })}
                className={inputClasses}
                rows={3}
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="10"
                  placeholder={t('page.vulnerabilities.field_cvss')}
                  value={formValues.cvss_score}
                  onChange={(e) => setFormValues({ ...formValues, cvss_score: e.target.value })}
                  className={inputClasses}
                />
                <select
                  value={formValues.severity}
                  onChange={(e) => setFormValues({ ...formValues, severity: e.target.value })}
                  className={inputClasses}
                  disabled={!!formValues.cvss_score}
                >
                  <option value="">{t('page.vulnerabilities.field_severity')}</option>
                  <option value="critical">{t('enum.vuln_severity.critical')}</option>
                  <option value="high">{t('enum.vuln_severity.high')}</option>
                  <option value="medium">{t('enum.vuln_severity.medium')}</option>
                  <option value="low">{t('enum.vuln_severity.low')}</option>
                  <option value="info">{t('enum.vuln_severity.info')}</option>
                </select>
              </div>
              <input
                placeholder={t('page.vulnerabilities.field_software')}
                value={formValues.affected_software}
                onChange={(e) => setFormValues({ ...formValues, affected_software: e.target.value })}
                className={inputClasses}
              />
              <input
                placeholder={t('page.vulnerabilities.field_versions')}
                value={formValues.affected_versions}
                onChange={(e) => setFormValues({ ...formValues, affected_versions: e.target.value })}
                className={inputClasses}
              />
              <textarea
                placeholder={t('page.vulnerabilities.field_remediation')}
                value={formValues.remediation_notes}
                onChange={(e) => setFormValues({ ...formValues, remediation_notes: e.target.value })}
                className={inputClasses}
                rows={2}
              />
              {formError && <p className="text-sm text-destructive">{formError}</p>}
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="h-9 rounded-md border border-border px-4 text-sm font-medium text-foreground hover:bg-muted/50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={create.isPending}
                  className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
                >
                  {create.isPending ? t('common.saving') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
