import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { ComplianceEvidencePanel } from '../../components/compliance/ComplianceEvidencePanel';
import { useI18n } from '../../lib/i18n';
import type { ComplianceDashboard, ControlAssessment, ComplianceStatusType } from '../../types';

const STATUS_OPTIONS: ComplianceStatusType[] = ['compliant', 'partial', 'non_compliant', 'not_assessed'];

function statusBadgeVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  if (status === 'compliant') return 'success';
  if (status === 'partial') return 'warning';
  if (status === 'non_compliant') return 'danger';
  return 'default';
}

export default function ComplianceDashboardPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [framework, setFramework] = useState<string>('');
  const [evidenceControl, setEvidenceControl] = useState<{ id: string; code: string } | null>(null);
  const [assessingControl, setAssessingControl] = useState<string | null>(null);
  const [assessStatus, setAssessStatus] = useState<ComplianceStatusType>('not_assessed');
  const [assessNotes, setAssessNotes] = useState('');
  const [exportTaskId, setExportTaskId] = useState<string | null>(null);

  const { data: dashboard, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['compliance-dashboard', framework],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (framework) params.framework = framework;
      const { data } = await api.get('/audit/compliance/dashboard', { params });
      return data as ComplianceDashboard;
    },
  });

  const { data: assessments, isLoading: assessmentsLoading } = useQuery({
    queryKey: ['compliance-assessments', framework],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (framework) params.framework = framework;
      const { data } = await api.get('/audit/compliance/assessments', { params });
      return data.data as ControlAssessment[];
    },
  });

  const assessMutation = useMutation({
    mutationFn: async ({ controlId, status, notes }: { controlId: string; status: string; notes: string }) => {
      await api.put(`/audit/compliance/controls/${controlId}/assessment`, { status, notes: notes || undefined });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['compliance-assessments'] });
      setAssessingControl(null);
    },
  });

  const exportMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/audit/compliance/export', { framework: framework || undefined });
      return data.task_id as string;
    },
    onSuccess: (taskId) => {
      setExportTaskId(taskId);
    },
  });

  const { data: exportStatus } = useQuery({
    queryKey: ['compliance-export', exportTaskId],
    queryFn: async () => {
      const { data } = await api.get(`/audit/compliance/export/${exportTaskId}/download`);
      return data as { task_id: string; status: string; download_url?: string | null };
    },
    enabled: !!exportTaskId,
    refetchInterval: exportTaskId ? 3000 : false,
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error).message} onRetry={refetch} />;
  if (!dashboard) return null;

  const frameworks = dashboard.frameworks.map((f) => f.framework);

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {t('compliance.title')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('compliance.subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/settings/compliance" className="text-sm text-primary hover:underline">
            {t('compliance.manage_controls')}
          </Link>
          {exportTaskId && exportStatus?.status === 'completed' && exportStatus.download_url ? (
            <a
              href={exportStatus.download_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-md bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"
            >
              {t('compliance.download')}
            </a>
          ) : (
            <button
              onClick={() => exportMutation.mutate()}
              disabled={exportMutation.isPending || (!!exportTaskId && exportStatus?.status !== 'completed')}
              className="rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {exportTaskId && exportStatus?.status !== 'completed'
                ? t('compliance.report_pending')
                : t('compliance.export_pdf')}
            </button>
          )}
        </div>
      </div>

      {/* Framework Filter */}
      <div className="flex items-end gap-3">
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">
            {t('compliance.framework_filter')}
          </label>
          <select
            value={framework}
            onChange={(e) => setFramework(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground"
          >
            <option value="">{t('compliance.all_frameworks')}</option>
            {frameworks.map((fw) => (
              <option key={fw} value={fw}>{fw}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label={t('compliance.overall_compliance')}
          value={`${dashboard.overall_compliance_pct}%`}
          variant={dashboard.overall_compliance_pct >= 80 ? 'success' : dashboard.overall_compliance_pct >= 50 ? 'warning' : 'danger'}
        />
        <StatCard label={t('compliance.compliant')} value={dashboard.compliant} variant="success" />
        <StatCard label={t('compliance.gaps')} value={dashboard.non_compliant + dashboard.not_assessed} variant="danger" />
        <StatCard
          label={t('compliance.evidence_coverage')}
          value={`${dashboard.total_controls > 0 ? Math.round(dashboard.controls_with_evidence / dashboard.total_controls * 100) : 0}%`}
        />
      </div>

      {/* Framework Breakdown */}
      {dashboard.frameworks.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">
            {t('compliance.framework_breakdown')}
          </h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-muted-foreground border-b border-border">
                <th className="text-left pb-2 font-medium">{t('compliance.framework_filter')}</th>
                <th className="text-right pb-2 font-medium">{t('compliance.compliant')}</th>
                <th className="text-right pb-2 font-medium">{t('compliance.partial')}</th>
                <th className="text-right pb-2 font-medium">{t('compliance.non_compliant')}</th>
                <th className="text-right pb-2 font-medium">{t('compliance.not_assessed')}</th>
                <th className="text-right pb-2 font-medium">%</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.frameworks.map((fw) => (
                <tr key={fw.framework} className="border-b border-border/50">
                  <td className="py-2 font-medium">{fw.framework}</td>
                  <td className="py-2 text-right"><Badge variant="success">{fw.compliant}</Badge></td>
                  <td className="py-2 text-right"><Badge variant="warning">{fw.partial}</Badge></td>
                  <td className="py-2 text-right">
                    {fw.non_compliant > 0 ? <Badge variant="danger">{fw.non_compliant}</Badge> : <Badge variant="default">0</Badge>}
                  </td>
                  <td className="py-2 text-right"><Badge variant="default">{fw.not_assessed}</Badge></td>
                  <td className="py-2 text-right font-medium">{fw.compliance_pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Gap Analysis */}
      {dashboard.gap_controls.length > 0 && (
        <div className="rounded-lg border border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-950/30 p-4">
          <h3 className="text-sm font-medium text-orange-800 dark:text-orange-300 mb-1">
            {t('compliance.gap_analysis')} — {dashboard.gap_controls.length} {t('compliance.gaps').toLowerCase()}
          </h3>
          <p className="text-xs text-muted-foreground mb-3">
            {t('compliance.gap_description')}
          </p>
          <div className="space-y-1">
            {dashboard.gap_controls.map((g) => (
              <div key={g.control_id} className="flex items-center justify-between text-sm py-1">
                <span>
                  <span className="font-mono text-xs text-muted-foreground mr-2">{g.control_code}</span>
                  <span className="text-foreground">{g.control_name}</span>
                  <span className="text-xs text-muted-foreground ml-2">({g.framework})</span>
                </span>
                <Badge variant={statusBadgeVariant(g.status)}>
                  {t(`compliance.${g.status === 'non_compliant' ? 'non_compliant' : 'not_assessed'}`)}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Control Assessments Table */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-3">
          {t('compliance.control_assessments')}
        </h3>
        {assessmentsLoading ? (
          <Loading />
        ) : !assessments || assessments.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('compliance.no_controls')}</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-muted-foreground border-b border-border">
                <th className="text-left pb-2 font-medium">{t('audit.controls.code')}</th>
                <th className="text-left pb-2 font-medium">{t('audit.controls.name_label')}</th>
                <th className="text-left pb-2 font-medium">{t('audit.controls.framework')}</th>
                <th className="text-left pb-2 font-medium">{t('compliance.status')}</th>
                <th className="text-right pb-2 font-medium">{t('compliance.evidence.title')}</th>
                <th className="text-right pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {assessments.map((a) => (
                <tr key={a.control_id} className="border-b border-border/50">
                  <td className="py-2 font-mono text-xs">{a.control_code}</td>
                  <td className="py-2">{a.control_name}</td>
                  <td className="py-2">{a.framework}</td>
                  <td className="py-2">
                    {assessingControl === a.control_id ? (
                      <div className="flex items-center gap-2">
                        <select
                          value={assessStatus}
                          onChange={(e) => setAssessStatus(e.target.value as ComplianceStatusType)}
                          className="rounded border border-input bg-background px-2 py-1 text-xs"
                        >
                          {STATUS_OPTIONS.map((s) => (
                            <option key={s} value={s}>{t(`compliance.${s === 'non_compliant' ? 'non_compliant' : s}`)}</option>
                          ))}
                        </select>
                        <input
                          value={assessNotes}
                          onChange={(e) => setAssessNotes(e.target.value)}
                          placeholder={t('compliance.notes_placeholder')}
                          className="rounded border border-input bg-background px-2 py-1 text-xs w-32"
                        />
                        <button
                          onClick={() => assessMutation.mutate({ controlId: a.control_id, status: assessStatus, notes: assessNotes })}
                          disabled={assessMutation.isPending}
                          className="rounded bg-primary px-2 py-1 text-xs text-primary-foreground"
                        >
                          {t('common.save')}
                        </button>
                        <button
                          onClick={() => setAssessingControl(null)}
                          className="text-xs text-muted-foreground"
                        >
                          {t('common.cancel')}
                        </button>
                      </div>
                    ) : (
                      <Badge variant={statusBadgeVariant(a.status)}>
                        {t(`compliance.${a.status === 'non_compliant' ? 'non_compliant' : a.status}`)}
                      </Badge>
                    )}
                  </td>
                  <td className="py-2 text-right">
                    <button
                      onClick={() => setEvidenceControl({ id: a.control_id, code: a.control_code })}
                      className="text-xs text-primary hover:underline"
                    >
                      {a.evidence_count} {t('compliance.view_evidence')}
                    </button>
                  </td>
                  <td className="py-2 text-right">
                    {assessingControl !== a.control_id && (
                      <button
                        onClick={() => {
                          setAssessingControl(a.control_id);
                          setAssessStatus(a.status);
                          setAssessNotes(a.notes || '');
                        }}
                        className="text-xs text-primary hover:underline"
                      >
                        {t('compliance.assess')}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Evidence Panel */}
      {evidenceControl && (
        <ComplianceEvidencePanel
          controlId={evidenceControl.id}
          controlCode={evidenceControl.code}
          onClose={() => setEvidenceControl(null)}
        />
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  variant,
}: {
  label: string;
  value: number | string;
  variant?: 'warning' | 'success' | 'info' | 'danger';
}) {
  const colors: Record<string, string> = {
    warning: 'text-yellow-600 dark:text-yellow-400',
    success: 'text-green-600 dark:text-green-400',
    info: 'text-blue-600 dark:text-blue-400',
    danger: 'text-red-600 dark:text-red-400',
  };

  return (
    <div className="rounded-lg border border-border bg-card px-4 py-3">
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className={`mt-1 text-2xl font-semibold ${variant ? colors[variant] : 'text-foreground'}`}>
        {value}
      </dd>
    </div>
  );
}
