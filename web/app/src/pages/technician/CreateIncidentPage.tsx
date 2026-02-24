import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { CustomFieldsForm } from '../../components/custom-fields/CustomFieldsForm';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';

export default function CreateIncidentPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { t } = useI18n();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [incidentType, setIncidentType] = useState('');
  const [severity, setSeverity] = useState('P2');
  const [detectedAt, setDetectedAt] = useState('');
  const [attackVector, setAttackVector] = useState('');
  const [dataBreachScope, setDataBreachScope] = useState('');
  const [customFieldsData, setCustomFieldsData] = useState<Record<string, unknown>>({});
  const [formError, setFormError] = useState('');

  const createMutation = useMutation({
    mutationFn: () => api.post('/incidents', {
      title,
      description,
      incident_type: incidentType,
      severity,
      detected_at: detectedAt ? new Date(detectedAt).toISOString() : null,
      attack_vector: attackVector || null,
      data_breach_scope: dataBreachScope || null,
      custom_fields_data: Object.keys(customFieldsData).length ? customFieldsData : undefined,
    }),
    onSuccess: (res) => {
      showToast({ title: t('page.create_incident.toast_created'), variant: 'success' });
      navigate(`/incidents/${res.data.data.id}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.create_incident.error_save');
      showToast({ title: detail, variant: 'error' });
    },
  });

  const submit = () => {
    if (!title.trim()) {
      setFormError(t('page.create_incident.error_title_required'));
      return;
    }
    if (!description.trim()) {
      setFormError(t('page.create_incident.error_description_required'));
      return;
    }
    if (!incidentType) {
      setFormError(t('page.create_incident.error_type_required'));
      return;
    }
    if (!detectedAt) {
      setFormError(t('page.create_incident.error_detected_at_required'));
      return;
    }
    setFormError('');
    createMutation.mutate();
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.create_incident.title')}</h2>

      <Card>
        {formError && (
          <div className="mb-3 rounded border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {formError}
          </div>
        )}
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="block mb-1.5 text-muted-foreground">{t('table.title')}</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} className="w-full" />
          </div>
          <div>
            <label className="block mb-1.5 text-muted-foreground">{t('table.type')}</label>
            <select value={incidentType} onChange={(e) => setIncidentType(e.target.value)} className="w-full">
              <option value="">{t('page.create_incident.select_type')}</option>
              {['phishing', 'malware', 'ransomware', 'data_breach', 'unauthorized_access', 'ddos', 'social_engineering', 'insider_threat', 'other'].map((t_) => (
                <option key={t_} value={t_}>{t(`enum.incident_type.${t_}`)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block mb-1.5 text-muted-foreground">{t('table.severity')}</label>
            <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="w-full">
              {['P1', 'P2', 'P3', 'P4'].map((s) => (
                <option key={s} value={s}>{t(`enum.incident_severity.${s}`)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block mb-1.5 text-muted-foreground">{t('page.create_incident.detected_at')}</label>
            <input type="datetime-local" value={detectedAt} onChange={(e) => setDetectedAt(e.target.value)} className="w-full" />
          </div>
          <div>
            <label className="block mb-1.5 text-muted-foreground">{t('page.create_incident.attack_vector')}</label>
            <input value={attackVector} onChange={(e) => setAttackVector(e.target.value)} className="w-full" placeholder={t('page.create_incident.attack_vector_placeholder')} />
          </div>
          <div className="md:col-span-2">
            <label className="block mb-1.5 text-muted-foreground">{t('table.description')}</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} className="w-full" />
          </div>
          <div className="md:col-span-2">
            <label className="block mb-1.5 text-muted-foreground">{t('page.create_incident.data_breach_scope')}</label>
            <textarea value={dataBreachScope} onChange={(e) => setDataBreachScope(e.target.value)} rows={2} className="w-full" placeholder={t('page.create_incident.data_breach_scope_placeholder')} />
          </div>
          <div className="md:col-span-2">
            <CustomFieldsForm
              entityType="incident"
              values={customFieldsData}
              onChange={setCustomFieldsData}
            />
          </div>
        </div>
      </Card>

      <div className="flex gap-2">
        <button
          onClick={submit}
          disabled={createMutation.isPending}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {createMutation.isPending ? t('common.working') : t('page.create_incident.submit')}
        </button>
        <button onClick={() => navigate('/incidents')} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
          {t('common.cancel')}
        </button>
      </div>
    </div>
  );
}
