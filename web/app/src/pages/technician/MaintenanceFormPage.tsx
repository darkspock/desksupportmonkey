import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { MaintenanceRecord, PaginatedResponse, User } from '../../types';

export default function MaintenanceFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { t } = useI18n();

  const [assetId, setAssetId] = useState('');
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [description, setDescription] = useState('');
  const [technicianId, setTechnicianId] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [checklistRaw, setChecklistRaw] = useState('');
  const preselectedAssetId = searchParams.get('asset_id') || '';
  const [formError, setFormError] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['maintenance-form', id],
    queryFn: async () => (await api.get(`/maintenance/${id}`)).data.data as MaintenanceRecord,
    enabled: isEdit,
  });

  const { data: techniciansData } = useQuery({
    queryKey: ['maintenance-technicians-options'],
    queryFn: async () => {
      const { data } = await api.get('/users', { params: { page: 1, page_size: 100, role: 'technician' } });
      return data as PaginatedResponse<User>;
    },
  });

  const technicians = techniciansData?.data ?? [];

  useEffect(() => {
    if (!data) return;
    setAssetId(data.asset_id);
    setTitle(data.title);
    setPriority(data.priority);
    setDescription(data.description || '');
    setTechnicianId(data.technician_id || '');
    setScheduledAt(data.scheduled_at ? data.scheduled_at.slice(0, 16) : '');
    setChecklistRaw(data.checklist_items.join('\n'));
  }, [data]);

  useEffect(() => {
    if (isEdit) return;
    if (!preselectedAssetId) return;
    setAssetId(preselectedAssetId);
  }, [isEdit, preselectedAssetId]);

  const checklistItems = useMemo(
    () => checklistRaw.split('\n').map((v) => v.trim()).filter(Boolean),
    [checklistRaw],
  );

  const payload = {
    title,
    priority,
    description: description || null,
    checklist_items: checklistItems,
    scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
  };

  const createMutation = useMutation({
    mutationFn: () => api.post('/maintenance', {
      ...payload,
      asset_id: assetId,
      technician_id: technicianId || null,
    }),
    onSuccess: (res) => {
      showToast({ title: t('page.maintenance_form.toast_created'), variant: 'success' });
      navigate(`/maintenance/${res.data.data.id}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.maintenance_form.error_save');
      showToast({ title: detail, variant: 'error' });
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => api.patch(`/maintenance/${id}`, payload),
    onSuccess: () => {
      showToast({ title: t('page.maintenance_form.toast_updated'), variant: 'success' });
      navigate(`/maintenance/${id}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.maintenance_form.error_save');
      showToast({ title: detail, variant: 'error' });
    },
  });

  const isSaving = createMutation.isPending || updateMutation.isPending;
  const submit = () => {
    if (!title.trim()) {
      setFormError(t('page.maintenance_form.error_title_required'));
      return;
    }
    if (!isEdit && !assetId.trim()) {
      setFormError(t('page.maintenance_form.error_asset_required'));
      return;
    }
    setFormError('');
    if (isEdit) updateMutation.mutate();
    else createMutation.mutate();
  };

  if (isEdit && isLoading) return <Loading />;
  if (isEdit && isError) return <ErrorState message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail} onRetry={() => { void refetch(); }} />;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">{isEdit ? t('page.maintenance_form.edit_title') : t('page.maintenance_form.new_title')}</h2>

      <Card>
        {formError && (
          <div className="mb-3 rounded border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {formError}
          </div>
        )}
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {!isEdit && (
            <>
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('table.asset')}</label>
                <input value={assetId} onChange={(e) => setAssetId(e.target.value)} className="w-full" />
              </div>
              <div>
                <label className="block mb-1.5 text-muted-foreground">{t('table.technician')}</label>
                <select
                  value={technicianId}
                  onChange={(e) => setTechnicianId(e.target.value)}
                  className="w-full"
                >
                  <option value="">{t('common.unassigned')}</option>
                  {technicians.map((tech) => (
                    <option key={tech.id} value={tech.id}>
                      {tech.email}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}
          <div>
            <label className="block mb-1.5 text-muted-foreground">{t('table.title')}</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} className="w-full" />
          </div>
          <div>
            <label className="block mb-1.5 text-muted-foreground">{t('table.priority')}</label>
            <select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full">
              {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((p) => <option key={p} value={p}>{t(`enum.maintenance_priority.${p.toLowerCase()}`)}</option>)}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="block mb-1.5 text-muted-foreground">{t('table.description')}</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} className="w-full" />
          </div>
          <div>
            <label className="block mb-1.5 text-muted-foreground">{t('table.date')}</label>
            <input type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} className="w-full" />
          </div>
          <div className="md:col-span-2">
            <label className="block mb-1.5 text-muted-foreground">{t('page.maintenance_form.checklist_help')}</label>
            <textarea value={checklistRaw} onChange={(e) => setChecklistRaw(e.target.value)} rows={5} className="w-full font-mono" />
          </div>
        </div>
      </Card>

      <div className="flex gap-2">
        <button
          onClick={submit}
          disabled={isSaving}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {isSaving ? t('common.working') : t('common.save')}
        </button>
        <button onClick={() => navigate(isEdit ? `/maintenance/${id}` : '/maintenance')} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
          {t('common.cancel')}
        </button>
      </div>
    </div>
  );
}
