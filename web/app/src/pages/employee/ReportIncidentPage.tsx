import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';

const INCIDENT_TYPES = [
  'malware',
  'data_breach',
  'ddos',
  'unauthorized_access',
  'phishing',
  'ransomware',
  'other',
];

export default function ReportIncidentPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const { showToast } = useToast();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [incidentType, setIncidentType] = useState('');

  const report = useMutation({
    mutationFn: (payload: { title: string; description: string; incident_type: string }) =>
      api.post('/my/report-incident', payload),
    onSuccess: () => {
      showToast({ title: t('page.report_incident.toast_reported'), variant: 'success' });
      navigate('/my/incidents');
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.report_incident.error');
      showToast({ title: detail, variant: 'error' });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim() || !incidentType) return;
    report.mutate({ title: title.trim(), description: description.trim(), incident_type: incidentType });
  };

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {t('page.report_incident.breadcrumb')}
        </p>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {t('page.report_incident.title')}
        </h1>
        <p className="text-sm text-muted-foreground">{t('page.report_incident.subtitle')}</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground">{t('page.report_incident.field_title')}</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
              className="mt-1 w-full"
              placeholder={t('page.report_incident.title_placeholder')}
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-foreground">{t('page.report_incident.field_type')}</label>
            <select
              value={incidentType}
              onChange={(e) => setIncidentType(e.target.value)}
              className="mt-1 w-full"
              required
            >
              <option value="">{t('page.report_incident.select_type')}</option>
              {INCIDENT_TYPES.map((type) => (
                <option key={type} value={type}>{t(`enum.incident_type.${type}`)}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-foreground">{t('page.report_incident.field_description')}</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={5}
              className="mt-1 w-full"
              placeholder={t('page.report_incident.description_placeholder')}
              required
            />
          </div>

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent transition-all"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={!title.trim() || !description.trim() || !incidentType || report.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {report.isPending ? t('common.working') : t('page.report_incident.btn_submit')}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
}
