import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';
import { CustomFieldsForm } from '../../components/custom-fields/CustomFieldsForm';
import { useAuth } from '../../contexts/AuthContext';
import { WorkflowIcon } from '../../components/ui/WorkflowIcon';
import { ClipboardList } from 'lucide-react';
import type { WorkflowTemplate } from '../../types';

// Map request subtypes to equipment profile asset types (for budget display)
const SUBTYPE_ASSET_MAP: Record<string, string[]> = {
  Computer: ['laptop'],
  Mobile: [],
  Peripheral: ['keyboard', 'mouse', 'headset', 'docking_station'],
  Monitor: ['monitor'],
  'Software License': [],
};

export default function NewRequestPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { isRole } = useAuth();
  const [searchParams] = useSearchParams();
  const onBehalfOf = searchParams.get('on_behalf_of');
  const onBehalfOfLabel = searchParams.get('on_behalf_of_label');
  const [form, setForm] = useState({
    templateId: '',
    type: '',
    title: '',
    description: '',
    subtype: '',
  });
  const [customFieldsData, setCustomFieldsData] = useState<Record<string, unknown>>({});

  // Fetch active workflow templates
  const templatesQuery = useQuery({
    queryKey: ['workflow-templates', { active: true }],
    queryFn: async () => {
      const { data } = await api.get('/workflow-templates?active=true');
      return data.data as WorkflowTemplate[];
    },
  });

  const templates = templatesQuery.data ?? [];
  const selectedTemplate = templates.find((t) => t.id === form.templateId);
  const subtypeOptions = (selectedTemplate?.subtypes ?? []).filter((s) => s.is_active);

  // Budget query for "New Equipment" type
  const isNewEquipment = selectedTemplate?.name === 'New Equipment';
  const budgetQuery = useQuery({
    queryKey: ['my-budget'],
    queryFn: async () => {
      const { data } = await api.get('/equipment-profiles/my-budget');
      return data.data as { items: { asset_type: string; budget_cents: number }[] };
    },
    enabled: isNewEquipment,
  });

  const matchingBudgets = (() => {
    if (!budgetQuery.data?.items?.length || !form.subtype) return [];
    const assetTypes = SUBTYPE_ASSET_MAP[form.subtype] ?? [];
    if (!assetTypes.length) return [];
    return budgetQuery.data.items.filter((b) => assetTypes.includes(b.asset_type));
  })();

  const showError = (msg: string) => {
    showToast({ title: msg, variant: 'error', durationMs: 5000 });
  };

  const mutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, unknown> = {
        type: form.type,
        title: form.title,
        description: form.description,
        template_id: form.templateId || undefined,
      };
      if (form.subtype) body.subtype = form.subtype;
      if (onBehalfOf) body.on_behalf_of = onBehalfOf;
      if (Object.keys(customFieldsData).length) body.custom_fields_data = customFieldsData;
      const { data } = await api.post('/requests', body);
      return data.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['my-requests'] });
      navigate(`/my/requests/${data.id}`);
    },
    onError: (err: unknown) => {
      showError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.new_request.error_create'),
      );
    },
  });

  const handleSubmit = () => {
    if (!form.templateId) {
      showError(t('page.new_request.error_type_required'));
      return;
    }
    if (!form.title.trim()) {
      showError(t('page.new_request.error_title_required'));
      return;
    }
    if (!form.description.trim()) {
      showError(t('page.new_request.error_description_required'));
      return;
    }
    mutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          {t('page.new_request.title')}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {t('page.new_request.subtitle')}
        </p>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} className="space-y-6">
        <div className="rounded-lg border border-border bg-card p-6 space-y-6">
          {onBehalfOfLabel && (
            <div className="flex items-center gap-2 rounded-md bg-primary/10 px-3 py-2 text-sm text-primary">
              <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
              </svg>
              {t('page.new_request.on_behalf_of')} <span className="font-medium">{onBehalfOfLabel}</span>
            </div>
          )}
          {/* Type selector cards */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-3">{t('page.new_request.type_label')}</label>
            {templatesQuery.isLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="h-24 rounded-lg border border-border bg-muted/30 animate-pulse" />
                ))}
              </div>
            ) : templatesQuery.isError ? (
              <div className="rounded-md border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
                {t('page.new_request.error_loading_types')}
              </div>
            ) : templates.length === 0 ? (
              <div className="rounded-md border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
                {t('page.new_request.no_types_available')}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {templates.map((tmpl) => (
                  <button
                    key={tmpl.id}
                    type="button"
                    onClick={() => setForm({ ...form, templateId: tmpl.id, type: tmpl.name, subtype: '' })}
                    className={`flex flex-col items-start gap-3 rounded-lg border p-4 text-left transition-all hover:border-primary ${
                      form.templateId === tmpl.id ? 'border-primary bg-primary/5' : 'border-border'
                    }`}
                  >
                    <div className={`flex h-10 w-10 items-center justify-center rounded-md ${
                      form.templateId === tmpl.id ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                    }`}>
                      {tmpl.icon ? <WorkflowIcon name={tmpl.icon} className="h-5 w-5" /> : <ClipboardList className="h-5 w-5" />}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">{tmpl.name}</p>
                      {tmpl.description && (
                        <p className="text-xs text-muted-foreground mt-0.5">{tmpl.description}</p>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Title + Subtype row */}
          <div className={`grid grid-cols-1 gap-4 ${subtypeOptions.length > 0 ? 'md:grid-cols-2' : ''}`}>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-foreground">{t('table.title')} *</label>
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full"
                placeholder={t('page.new_request.title_placeholder')}
              />
            </div>
            {subtypeOptions.length > 0 && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">{t('page.new_request.subtype')}</label>
                <select
                  value={form.subtype}
                  onChange={(e) => setForm({ ...form, subtype: e.target.value })}
                  className="w-full"
                >
                  <option value="">{t('page.new_request.select_subtype')}</option>
                  {subtypeOptions.map((sub) => (
                    <option key={sub.id} value={sub.name}>{sub.name}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Budget indicator for New Equipment */}
          {isNewEquipment && form.subtype && (
            <div className="flex items-center gap-2 rounded-md border border-border bg-muted/50 px-3 py-2 text-sm">
              <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
              {matchingBudgets.length > 0 ? (
                <span className="text-foreground">
                  {matchingBudgets.map((b) => (
                    <span key={b.asset_type}>
                      {t('page.new_request.budget_amount', { amount: (b.budget_cents / 100).toLocaleString() })}
                      {' '}
                      <span className="text-muted-foreground">({t(`enum.${b.asset_type}`)})</span>
                    </span>
                  ))}
                </span>
              ) : (
                <span className="text-muted-foreground">{t('page.new_request.no_budget_set')}</span>
              )}
            </div>
          )}

          {/* Description */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">{t('table.description')} *</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={5}
              className="w-full resize-none"
              placeholder={t('page.new_request.description_placeholder')}
            />
            <p className="text-xs text-muted-foreground">
              {t('page.new_request.description_hint')}
            </p>
          </div>

          {/* Custom Fields */}
          <CustomFieldsForm
            entityType="request"
            values={customFieldsData}
            onChange={setCustomFieldsData}
            isEmployee={isRole('employee')}
          />
        </div>

        {/* Buttons — right-aligned */}
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
          >
            {t('common.cancel')}
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {mutation.isPending ? t('page.new_request.submitting') : t('page.new_request.submit')}
          </button>
        </div>
      </form>
    </div>
  );
}
