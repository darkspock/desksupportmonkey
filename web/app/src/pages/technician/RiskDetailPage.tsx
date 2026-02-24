import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/ui/Toast';
import type { RiskDetail } from '../../types';

const levelVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  low: 'success',
  medium: 'info',
  high: 'warning',
  critical: 'danger',
};

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger' | 'purple'> = {
  open: 'warning',
  under_review: 'info',
  mitigated: 'success',
  accepted: 'purple',
  closed: 'default',
};

const mitStatusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  open: 'warning',
  in_progress: 'info',
  completed: 'success',
  cancelled: 'default',
};

export default function RiskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useI18n();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const toast = useToast();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  const [showAssess, setShowAssess] = useState(false);
  const [likelihood, setLikelihood] = useState(3);
  const [impact, setImpact] = useState(3);
  const [showStatus, setShowStatus] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [showTreatment, setShowTreatment] = useState(false);
  const [newTreatment, setNewTreatment] = useState('');
  const [showAddMitigation, setShowAddMitigation] = useState(false);
  const [mitDescription, setMitDescription] = useState('');
  const [showAddLink, setShowAddLink] = useState(false);
  const [linkType, setLinkType] = useState('asset');
  const [linkEntityId, setLinkEntityId] = useState('');

  const { data: risk, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['risk', id],
    queryFn: async () => {
      const { data } = await api.get(`/risks/${id}`);
      return data.data as RiskDetail;
    },
  });

  const assessMut = useMutation({
    mutationFn: async () => {
      await api.post(`/risks/${id}/assess`, { likelihood, impact });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk', id] });
      setShowAssess(false);
      toast.success(t('page.risks.assessed'));
    },
  });

  const statusMut = useMutation({
    mutationFn: async () => {
      await api.post(`/risks/${id}/status`, { status: newStatus });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk', id] });
      setShowStatus(false);
      toast.success(t('page.risks.status_changed'));
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Error');
    },
  });

  const treatmentMut = useMutation({
    mutationFn: async () => {
      await api.post(`/risks/${id}/treatment`, { treatment: newTreatment });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk', id] });
      setShowTreatment(false);
      toast.success(t('page.risks.treatment_set'));
    },
  });

  const addMitMut = useMutation({
    mutationFn: async () => {
      await api.post(`/risks/${id}/mitigations`, { description: mitDescription });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk', id] });
      setShowAddMitigation(false);
      setMitDescription('');
      toast.success(t('page.risks.mitigation_added'));
    },
  });

  const addLinkMut = useMutation({
    mutationFn: async () => {
      await api.post(`/risks/${id}/links`, { link_type: linkType, link_id: linkEntityId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk', id] });
      setShowAddLink(false);
      setLinkEntityId('');
      toast.success(t('page.risks.link_added'));
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Error');
    },
  });

  const deleteMut = useMutation({
    mutationFn: async () => {
      await api.delete(`/risks/${id}`);
    },
    onSuccess: () => {
      toast.success(t('page.risks.deleted'));
      navigate('/risks');
    },
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error).message} onRetry={refetch} />;
  if (!risk) return null;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Link to="/risks" className="hover:text-foreground">{t('page.risks.title')}</Link>
            <span>/</span>
            <span>{risk.id.slice(0, 8)}</span>
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{risk.title}</h2>
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            <Link
              to={`/risks/${id}/edit`}
              className="inline-flex h-9 items-center rounded-md border border-border bg-card px-4 text-sm font-medium text-foreground hover:bg-muted/50"
            >
              {t('common.edit')}
            </Link>
            <button
              onClick={() => { if (confirm(t('page.risks.confirm_delete'))) deleteMut.mutate(); }}
              className="inline-flex h-9 items-center rounded-md border border-destructive/30 bg-card px-4 text-sm font-medium text-destructive hover:bg-destructive/10"
            >
              {t('common.delete')}
            </button>
          </div>
        )}
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <InfoCard label={t('risk.field.category')} value={t(`risk.category.${risk.category}`)} />
        <InfoCard
          label={t('risk.field.status')}
          value={<Badge variant={statusVariant[risk.status] || 'default'}>{t(`risk.status.${risk.status}`)}</Badge>}
        />
        <InfoCard
          label={t('risk.field.level')}
          value={
            risk.risk_level ? (
              <Badge variant={levelVariant[risk.risk_level] || 'default'}>{t(`risk.level.${risk.risk_level}`)}</Badge>
            ) : '—'
          }
        />
        <InfoCard
          label={t('risk.field.treatment')}
          value={risk.treatment ? t(`risk.treatment.${risk.treatment}`) : '—'}
        />
      </div>

      {/* Scoring */}
      {risk.likelihood && risk.impact && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">{t('page.risks.scoring')}</h3>
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-foreground">{risk.likelihood}</div>
              <div className="text-xs text-muted-foreground">{t('risk.field.likelihood')}</div>
            </div>
            <span className="text-xl text-muted-foreground">×</span>
            <div className="text-center">
              <div className="text-2xl font-bold text-foreground">{risk.impact}</div>
              <div className="text-xs text-muted-foreground">{t('risk.field.impact')}</div>
            </div>
            <span className="text-xl text-muted-foreground">=</span>
            <div className="text-center">
              <Badge variant={levelVariant[risk.risk_level || ''] || 'default'} className="text-lg px-3 py-1">
                {risk.risk_level ? t(`risk.level.${risk.risk_level}`) : '—'}
              </Badge>
            </div>
          </div>
        </div>
      )}

      {/* Description */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-2">{t('risk.field.description')}</h3>
        <p className="text-sm text-foreground whitespace-pre-wrap">{risk.description}</p>
      </div>

      {/* Details */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <InfoCard label={t('risk.field.owner')} value={risk.owner_name || '—'} />
        <InfoCard label={t('risk.field.created_by')} value={risk.created_by_name || risk.created_by} />
        <InfoCard label={t('risk.field.review_cadence')} value={risk.review_cadence ? t(`risk.cadence.${risk.review_cadence}`) : '—'} />
        <InfoCard label={t('risk.field.next_review')} value={risk.next_review_at ? formatDateTime(risk.next_review_at) : '—'} />
      </div>

      {/* Admin Actions */}
      {isAdmin && risk.status !== 'closed' && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setShowAssess(!showAssess)}
            className="inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            {t('page.risks.assess')}
          </button>
          <button
            onClick={() => setShowStatus(!showStatus)}
            className="inline-flex h-9 items-center rounded-md border border-border bg-card px-4 text-sm font-medium text-foreground hover:bg-muted/50"
          >
            {t('page.risks.change_status')}
          </button>
          <button
            onClick={() => setShowTreatment(!showTreatment)}
            className="inline-flex h-9 items-center rounded-md border border-border bg-card px-4 text-sm font-medium text-foreground hover:bg-muted/50"
          >
            {t('page.risks.set_treatment')}
          </button>
        </div>
      )}

      {/* Assess Form */}
      {showAssess && (
        <div className="rounded-lg border border-border bg-card p-4 flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-xs text-muted-foreground mb-1">{t('risk.field.likelihood')} (1-5)</label>
            <input type="number" min={1} max={5} value={likelihood} onChange={e => setLikelihood(Number(e.target.value))}
              className="h-9 w-20 rounded-md border border-border bg-background px-3 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1">{t('risk.field.impact')} (1-5)</label>
            <input type="number" min={1} max={5} value={impact} onChange={e => setImpact(Number(e.target.value))}
              className="h-9 w-20 rounded-md border border-border bg-background px-3 text-sm" />
          </div>
          <button onClick={() => assessMut.mutate()} disabled={assessMut.isPending}
            className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {t('common.save')}
          </button>
        </div>
      )}

      {/* Status Form */}
      {showStatus && (
        <div className="rounded-lg border border-border bg-card p-4 flex items-end gap-4">
          <div>
            <label className="block text-xs text-muted-foreground mb-1">{t('risk.field.status')}</label>
            <select value={newStatus} onChange={e => setNewStatus(e.target.value)}
              className="h-9 rounded-md border border-border bg-background px-3 text-sm">
              <option value="">{t('common.select')}</option>
              {['open', 'under_review', 'mitigated', 'accepted', 'closed'].map(s => (
                <option key={s} value={s}>{t(`risk.status.${s}`)}</option>
              ))}
            </select>
          </div>
          <button onClick={() => statusMut.mutate()} disabled={!newStatus || statusMut.isPending}
            className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {t('common.save')}
          </button>
        </div>
      )}

      {/* Treatment Form */}
      {showTreatment && (
        <div className="rounded-lg border border-border bg-card p-4 flex items-end gap-4">
          <div>
            <label className="block text-xs text-muted-foreground mb-1">{t('risk.field.treatment')}</label>
            <select value={newTreatment} onChange={e => setNewTreatment(e.target.value)}
              className="h-9 rounded-md border border-border bg-background px-3 text-sm">
              <option value="">{t('common.select')}</option>
              {['mitigate', 'accept', 'transfer', 'avoid'].map(tr => (
                <option key={tr} value={tr}>{t(`risk.treatment.${tr}`)}</option>
              ))}
            </select>
          </div>
          <button onClick={() => treatmentMut.mutate()} disabled={!newTreatment || treatmentMut.isPending}
            className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {t('common.save')}
          </button>
        </div>
      )}

      {/* Mitigations */}
      <div className="rounded-lg border border-border bg-card">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h3 className="text-sm font-medium text-foreground">{t('page.risks.mitigations')} ({risk.mitigations.length})</h3>
          {isAdmin && risk.status !== 'closed' && (
            <button onClick={() => setShowAddMitigation(!showAddMitigation)}
              className="text-xs text-primary hover:underline">
              + {t('page.risks.add_mitigation')}
            </button>
          )}
        </div>
        {showAddMitigation && (
          <div className="border-b border-border px-4 py-3 flex gap-3 items-end">
            <div className="flex-1">
              <input type="text" value={mitDescription} onChange={e => setMitDescription(e.target.value)}
                placeholder={t('page.risks.mitigation_placeholder')}
                className="h-9 w-full rounded-md border border-border bg-background px-3 text-sm" />
            </div>
            <button onClick={() => addMitMut.mutate()} disabled={!mitDescription.trim() || addMitMut.isPending}
              className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
              {t('common.add')}
            </button>
          </div>
        )}
        {risk.mitigations.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-muted-foreground">{t('page.risks.no_mitigations')}</p>
        ) : (
          <div className="divide-y divide-border">
            {risk.mitigations.map(m => (
              <div key={m.id} className="px-4 py-3 flex items-center justify-between">
                <div>
                  <p className="text-sm text-foreground">{m.description}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {m.owner_name && <span>{m.owner_name} · </span>}
                    {m.target_date && <span>{m.target_date} · </span>}
                    <Badge variant={mitStatusVariant[m.status] || 'default'} className="text-[10px]">
                      {t(`risk.mitigation_status.${m.status}`)}
                    </Badge>
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Links */}
      <div className="rounded-lg border border-border bg-card">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h3 className="text-sm font-medium text-foreground">{t('page.risks.links')} ({risk.links.length})</h3>
          {isAdmin && risk.status !== 'closed' && (
            <button onClick={() => setShowAddLink(!showAddLink)}
              className="text-xs text-primary hover:underline">
              + {t('page.risks.add_link')}
            </button>
          )}
        </div>
        {showAddLink && (
          <div className="border-b border-border px-4 py-3 flex gap-3 items-end">
            <select value={linkType} onChange={e => setLinkType(e.target.value)}
              className="h-9 rounded-md border border-border bg-background px-3 text-sm">
              <option value="asset">{t('risk.link_type.asset')}</option>
              <option value="department">{t('risk.link_type.department')}</option>
              <option value="vendor">{t('risk.link_type.vendor')}</option>
            </select>
            <input type="text" value={linkEntityId} onChange={e => setLinkEntityId(e.target.value)}
              placeholder={t('page.risks.link_id_placeholder')}
              className="h-9 flex-1 rounded-md border border-border bg-background px-3 text-sm" />
            <button onClick={() => addLinkMut.mutate()} disabled={!linkEntityId.trim() || addLinkMut.isPending}
              className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
              {t('common.add')}
            </button>
          </div>
        )}
        {risk.links.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-muted-foreground">{t('page.risks.no_links')}</p>
        ) : (
          <div className="divide-y divide-border">
            {risk.links.map(l => (
              <div key={l.id} className="px-4 py-3 flex items-center justify-between">
                <div>
                  <Badge variant="default" className="mr-2">{t(`risk.link_type.${l.link_type}`)}</Badge>
                  <span className="text-sm font-mono text-muted-foreground">{l.link_id.slice(0, 12)}...</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* History */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <h3 className="text-sm font-medium text-foreground">{t('page.risks.history')}</h3>
        </div>
        {risk.history.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-muted-foreground">{t('page.risks.no_history')}</p>
        ) : (
          <div className="divide-y divide-border">
            {risk.history.map(h => (
              <div key={h.id} className="px-4 py-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-foreground">{h.description}</p>
                  <span className="text-xs text-muted-foreground">{h.created_at ? formatDateTime(h.created_at) : ''}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">{h.actor_name || h.actor_id.slice(0, 8)}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Meta */}
      <div className="text-xs text-muted-foreground">
        {t('common.created')}: {risk.created_at ? formatDateTime(risk.created_at) : '—'}
        {risk.updated_at && <> · {t('common.updated')}: {formatDateTime(risk.updated_at)}</>}
      </div>
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-card px-4 py-3">
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-sm text-foreground">{value}</dd>
    </div>
  );
}
