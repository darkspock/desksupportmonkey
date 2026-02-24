import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../ui/Loading';
import { Badge } from '../ui/Badge';
import { useI18n } from '../../lib/i18n';
import type { ComplianceEvidence, EvidenceTypeValue } from '../../types';

interface Props {
  controlId: string;
  controlCode: string;
  onClose: () => void;
}

const EVIDENCE_TYPES: EvidenceTypeValue[] = ['audit_log', 'incident', 'risk', 'sla', 'manual'];

export function ComplianceEvidencePanel({ controlId, controlCode, onClose }: Props) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [formType, setFormType] = useState<EvidenceTypeValue>('manual');
  const [formTitle, setFormTitle] = useState('');
  const [formRefId, setFormRefId] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formUrl, setFormUrl] = useState('');

  const { data: evidence, isLoading } = useQuery({
    queryKey: ['compliance-evidence', controlId],
    queryFn: async () => {
      const { data } = await api.get(`/audit/compliance/controls/${controlId}/evidence`);
      return data.data as ComplianceEvidence[];
    },
  });

  const addMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/audit/compliance/controls/${controlId}/evidence`, {
        evidence_type: formType,
        title: formTitle,
        reference_id: formRefId || undefined,
        description: formDesc || undefined,
        url: formUrl || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance-evidence', controlId] });
      queryClient.invalidateQueries({ queryKey: ['compliance-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['compliance-assessments'] });
      setShowForm(false);
      setFormTitle('');
      setFormRefId('');
      setFormDesc('');
      setFormUrl('');
    },
  });

  const removeMutation = useMutation({
    mutationFn: async (evidenceId: string) => {
      await api.delete(`/audit/compliance/evidence/${evidenceId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance-evidence', controlId] });
      queryClient.invalidateQueries({ queryKey: ['compliance-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['compliance-assessments'] });
    },
  });

  const typeLabel = (et: EvidenceTypeValue) => t(`compliance.evidence.type_${et}`);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button type="button" className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative z-10 w-full max-w-lg bg-card border-l border-border h-full overflow-y-auto flex flex-col">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">
            {t('compliance.evidence.title')} — {controlCode}
          </h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xl leading-none">&times;</button>
        </div>

        <div className="flex-1 p-4">
          {isLoading ? (
            <Loading />
          ) : !evidence || evidence.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t('compliance.evidence.no_evidence')}</p>
          ) : (
            <div className="space-y-3">
              {evidence.map((e) => (
                <div key={e.id} className="rounded-md border border-border p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="default">{typeLabel(e.evidence_type)}</Badge>
                        <span className="text-sm font-medium text-foreground truncate">{e.title}</span>
                      </div>
                      {e.description && (
                        <p className="text-xs text-muted-foreground mt-1">{e.description}</p>
                      )}
                      {e.reference_id && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Ref: <span className="font-mono">{e.reference_id}</span>
                        </p>
                      )}
                      {e.url && (
                        <a href={e.url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline mt-1 block truncate">
                          {e.url}
                        </a>
                      )}
                    </div>
                    <button
                      onClick={() => removeMutation.mutate(e.id)}
                      className="text-xs text-red-600 hover:text-red-800 shrink-0"
                    >
                      {t('compliance.evidence.remove')}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {!showForm ? (
            <button
              onClick={() => setShowForm(true)}
              className="mt-4 w-full rounded-md border border-dashed border-border py-2 text-sm text-muted-foreground hover:border-primary hover:text-primary transition-colors"
            >
              + {t('compliance.evidence.add')}
            </button>
          ) : (
            <div className="mt-4 rounded-md border border-border p-3 space-y-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  {t('compliance.evidence.type')}
                </label>
                <select
                  value={formType}
                  onChange={(e) => setFormType(e.target.value as EvidenceTypeValue)}
                  className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                >
                  {EVIDENCE_TYPES.map((et) => (
                    <option key={et} value={et}>{typeLabel(et)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  {t('compliance.evidence.title_label')}
                </label>
                <input
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                  placeholder="Evidence title..."
                />
              </div>
              {formType !== 'manual' && (
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">
                    {t('compliance.evidence.reference_id')}
                  </label>
                  <input
                    value={formRefId}
                    onChange={(e) => setFormRefId(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                    placeholder="ID from other system..."
                  />
                </div>
              )}
              {formType === 'manual' && (
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">
                    {t('compliance.evidence.url')}
                  </label>
                  <input
                    value={formUrl}
                    onChange={(e) => setFormUrl(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                    placeholder="https://..."
                  />
                </div>
              )}
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  {t('compliance.evidence.description')}
                </label>
                <textarea
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  rows={2}
                  className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => addMutation.mutate()}
                  disabled={!formTitle.trim() || addMutation.isPending}
                  className="rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {t('compliance.evidence.add')}
                </button>
                <button
                  onClick={() => setShowForm(false)}
                  className="rounded-md border border-input px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground"
                >
                  {t('common.cancel')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
