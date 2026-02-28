import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Shield, ShieldAlert, FileText, ClipboardCheck, Network, AlertTriangle, Bug } from 'lucide-react';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { ErrorState, EmptyState } from '../../components/ui/StateBlock';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Table, Th, Td } from '../../components/ui/Table';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { useI18n } from '../../lib/i18n';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../hooks/useToast';
import { formatDate, formatDateTime } from '../../lib/date';
import type {
  VendorRiskProfile,
  VendorContract,
  VendorRiskAssessment,
  VendorDependency,
  PaginatedResponse,
} from '../../types';

type TabKey = 'overview' | 'contracts' | 'assessments' | 'dependencies' | 'incidents' | 'risks';

const RISK_VARIANT: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
  low: 'success',
  medium: 'warning',
  high: 'danger',
  critical: 'danger',
};

const STATUS_VARIANT: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'default'> = {
  draft: 'default',
  active: 'success',
  expired: 'warning',
  terminated: 'danger',
};

const SEVERITY_VARIANT: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'default'> = {
  p1: 'danger',
  p2: 'danger',
  p3: 'warning',
  p4: 'info',
  p5: 'default',
};

// ── Tab button ──────────────────────────────────────────
function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active
          ? 'border-primary text-primary'
          : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
      }`}
    >
      {children}
    </button>
  );
}

// ── Score bar ───────────────────────────────────────────
function ScoreBar({ label, score }: { label: string; score: number }) {
  const pct = (score / 5) * 100;
  const color = score <= 2 ? 'bg-green-500' : score <= 3 ? 'bg-yellow-500' : score <= 4 ? 'bg-orange-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-3">
      <span className="w-40 text-sm text-muted-foreground truncate">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-muted">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-6 text-sm font-medium text-right">{score}</span>
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// Main Component
// ═══════════════════════════════════════════════════════
export default function VendorDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin' || user?.role === 'procurement_manager';

  const [tab, setTab] = useState<TabKey>('overview');

  // ── Risk Profile ──────────────────────────────────────
  const { data: profile, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['vendor-risk-profile', id],
    queryFn: async () => {
      const { data } = await api.get(`/vendors/${id}/risk-profile`);
      return data.data as VendorRiskProfile;
    },
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('vendor_detail.error_load')} onRetry={() => { void refetch(); }} />;
  if (!profile) return <EmptyState message={t('vendor_detail.not_found')} />;

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Link to="/vendors" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-3">
          <ArrowLeft className="h-4 w-4" />
          {t('vendor_detail.back_to_list')}
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-semibold tracking-tight text-foreground">{profile.name}</h2>
              {profile.is_critical_ict && (
                <Badge variant="danger"><ShieldAlert className="h-3 w-3 mr-1" />{t('vendor_detail.critical_ict')}</Badge>
              )}
              {profile.risk_level && (
                <Badge variant={RISK_VARIANT[profile.risk_level] ?? 'info'}>
                  {t(`page.vendors.risk_${profile.risk_level}`)}
                </Badge>
              )}
              <Badge variant={profile.is_active ? 'success' : 'danger'}>
                {profile.is_active ? t('page.vendors.active') : t('page.vendors.inactive')}
              </Badge>
            </div>
            {(profile.contact_email || profile.phone) && (
              <p className="mt-1 text-sm text-muted-foreground">
                {[profile.contact_email, profile.phone].filter(Boolean).join(' · ')}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border mb-6 overflow-x-auto">
        <TabBtn active={tab === 'overview'} onClick={() => setTab('overview')}>{t('vendor_detail.tab_overview')}</TabBtn>
        <TabBtn active={tab === 'contracts'} onClick={() => setTab('contracts')}>{t('vendor_detail.tab_contracts')}</TabBtn>
        <TabBtn active={tab === 'assessments'} onClick={() => setTab('assessments')}>{t('vendor_detail.tab_assessments')}</TabBtn>
        <TabBtn active={tab === 'dependencies'} onClick={() => setTab('dependencies')}>{t('vendor_detail.tab_dependencies')}</TabBtn>
        <TabBtn active={tab === 'incidents'} onClick={() => setTab('incidents')}>{t('vendor_detail.tab_incidents')}</TabBtn>
        <TabBtn active={tab === 'risks'} onClick={() => setTab('risks')}>{t('vendor_detail.tab_risks')}</TabBtn>
      </div>

      {/* Tab Content */}
      {tab === 'overview' && <OverviewTab profile={profile} t={t} />}
      {tab === 'contracts' && <ContractsTab vendorId={id!} isAdmin={isAdmin} t={t} queryClient={queryClient} showToast={showToast} />}
      {tab === 'assessments' && <AssessmentsTab vendorId={id!} isAdmin={isAdmin} t={t} queryClient={queryClient} showToast={showToast} />}
      {tab === 'dependencies' && <DependenciesTab vendorId={id!} isAdmin={isAdmin} t={t} queryClient={queryClient} showToast={showToast} />}
      {tab === 'incidents' && <IncidentsTab profile={profile} t={t} />}
      {tab === 'risks' && <RisksTab profile={profile} t={t} />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// Overview Tab
// ═══════════════════════════════════════════════════════
function OverviewTab({ profile, t }: { profile: VendorRiskProfile; t: (k: string) => string }) {
  const a = profile.latest_assessment;
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Info Card */}
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-foreground mb-4">{t('vendor_detail.vendor_info')}</h3>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between"><dt className="text-muted-foreground">{t('vendor_detail.category')}</dt><dd>{profile.category ? t(`page.vendors.cat_${profile.category}`) : '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-muted-foreground">{t('vendor_detail.website')}</dt><dd>{profile.website ? <a href={profile.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{profile.website}</a> : '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-muted-foreground">{t('vendor_detail.address')}</dt><dd>{profile.address || '—'}</dd></div>
        </dl>
      </Card>

      {/* Quick Stats */}
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-foreground mb-4">{t('vendor_detail.quick_stats')}</h3>
        <div className="grid grid-cols-2 gap-4">
          <StatBlock icon={<FileText className="h-4 w-4" />} label={t('vendor_detail.active_contracts')} value={profile.active_contracts_count} />
          <StatBlock icon={<FileText className="h-4 w-4 text-muted-foreground" />} label={t('vendor_detail.total_contracts')} value={profile.total_contracts_count} />
          <StatBlock icon={<Network className="h-4 w-4" />} label={t('vendor_detail.dependencies')} value={profile.dependency_count} />
          <StatBlock icon={<ShieldAlert className="h-4 w-4 text-destructive" />} label={t('vendor_detail.critical_deps')} value={profile.critical_dependency_count} />
          <StatBlock icon={<Bug className="h-4 w-4" />} label={t('vendor_detail.incidents')} value={profile.incident_count} />
          <StatBlock icon={<AlertTriangle className="h-4 w-4" />} label={t('vendor_detail.linked_risks')} value={profile.risk_count} />
        </div>
      </Card>

      {/* Latest Assessment */}
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-foreground mb-4">{t('vendor_detail.latest_assessment')}</h3>
        {a ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between mb-2">
              <Badge variant={RISK_VARIANT[a.overall_risk_level] ?? 'info'}>{a.overall_risk_level}</Badge>
              <span className="text-xs text-muted-foreground">{formatDate(a.assessment_date)}</span>
            </div>
            <ScoreBar label={t('vendor_detail.score_data_handling')} score={a.data_handling_score} />
            <ScoreBar label={t('vendor_detail.score_security_certs')} score={a.security_certs_score} />
            <ScoreBar label={t('vendor_detail.score_incident_response')} score={a.incident_response_score} />
            <ScoreBar label={t('vendor_detail.score_business_continuity')} score={a.business_continuity_score} />
            <ScoreBar label={t('vendor_detail.score_subcontractor')} score={a.subcontractor_score} />
            {a.next_review_date && (
              <p className="text-xs text-muted-foreground mt-2">{t('vendor_detail.next_review')}: {formatDate(a.next_review_date)}</p>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">{t('vendor_detail.no_assessments')}</p>
        )}
      </Card>
    </div>
  );
}

function StatBlock({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center justify-center h-8 w-8 rounded-md bg-muted">{icon}</div>
      <div>
        <p className="text-lg font-semibold text-foreground">{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// Contracts Tab
// ═══════════════════════════════════════════════════════
function ContractsTab({ vendorId, isAdmin, t, queryClient, showToast }: {
  vendorId: string; isAdmin: boolean; t: (k: string, p?: Record<string, string>) => string;
  queryClient: ReturnType<typeof useQueryClient>; showToast: (o: { title: string; variant?: string }) => void;
}) {
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [contractType, setContractType] = useState('service');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [renewalDate, setRenewalDate] = useState('');
  const [autoRenewal, setAutoRenewal] = useState(false);
  const [annualValue, setAnnualValue] = useState('');
  const [currency, setCurrency] = useState('EUR');
  const [notes, setNotes] = useState('');
  const [securityClauses, setSecurityClauses] = useState<Record<string, boolean>>({
    data_processing_agreement: false,
    breach_notification_clause: false,
    audit_rights: false,
    subprocessor_restrictions: false,
    data_location_clause: false,
    termination_data_return: false,
  });
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const pageSize = 10;

  const { data, isLoading } = useQuery({
    queryKey: ['vendor-contracts', vendorId, page],
    queryFn: async () => {
      const { data } = await api.get(`/vendors/${vendorId}/contracts?page=${page}&page_size=${pageSize}`);
      return data as PaginatedResponse<VendorContract>;
    },
  });

  const contracts = data?.data ?? [];
  const total = data?.meta?.total ?? 0;

  const resetForm = () => {
    setShowForm(false); setEditId(null); setTitle(''); setContractType('service');
    setStartDate(''); setEndDate(''); setRenewalDate(''); setAutoRenewal(false);
    setAnnualValue(''); setCurrency('EUR'); setNotes('');
    setSecurityClauses({
      data_processing_agreement: false, breach_notification_clause: false,
      audit_rights: false, subprocessor_restrictions: false,
      data_location_clause: false, termination_data_return: false,
    });
  };

  const openEdit = (c: VendorContract) => {
    setEditId(c.id); setTitle(c.title); setContractType(c.contract_type);
    setStartDate(c.start_date); setEndDate(c.end_date || '');
    setRenewalDate(c.renewal_date || ''); setAutoRenewal(c.auto_renewal);
    setAnnualValue(c.annual_value != null ? String(c.annual_value) : '');
    setCurrency(c.currency || 'EUR'); setNotes(c.notes || '');
    setSecurityClauses(c.security_clauses || {});
    setShowForm(true);
  };

  const saveMut = useMutation({
    mutationFn: async () => {
      const payload = {
        title, contract_type: contractType, start_date: startDate,
        end_date: endDate || null, renewal_date: renewalDate || null,
        auto_renewal: autoRenewal,
        annual_value: annualValue ? Number(annualValue) : null,
        currency: currency || null, notes: notes || null,
        security_clauses: securityClauses,
      };
      if (editId) {
        await api.put(`/vendors/${vendorId}/contracts/${editId}`, payload);
      } else {
        await api.post(`/vendors/${vendorId}/contracts`, payload);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-contracts', vendorId] });
      queryClient.invalidateQueries({ queryKey: ['vendor-risk-profile', vendorId] });
      resetForm();
      showToast({ title: editId ? t('vendor_detail.contract_updated') : t('vendor_detail.contract_created'), variant: 'success' });
    },
  });

  const deleteMut = useMutation({
    mutationFn: async (contractId: string) => {
      await api.delete(`/vendors/${vendorId}/contracts/${contractId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-contracts', vendorId] });
      queryClient.invalidateQueries({ queryKey: ['vendor-risk-profile', vendorId] });
      setPendingDelete(null);
      showToast({ title: t('vendor_detail.contract_deleted'), variant: 'success' });
    },
  });

  const changeStatusMut = useMutation({
    mutationFn: async ({ contractId, status }: { contractId: string; status: string }) => {
      await api.post(`/vendors/${vendorId}/contracts/${contractId}/status`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-contracts', vendorId] });
      queryClient.invalidateQueries({ queryKey: ['vendor-risk-profile', vendorId] });
    },
  });

  return (
    <div>
      {isAdmin && (
        <div className="mb-4 flex justify-end">
          <button onClick={() => { resetForm(); setShowForm(true); }} className="inline-flex items-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs hover:bg-primary/90">
            {t('vendor_detail.add_contract')}
          </button>
        </div>
      )}

      <Card>
        {isLoading ? <Loading /> : !contracts.length ? <EmptyState message={t('vendor_detail.no_contracts')} /> : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>{t('vendor_detail.contract_title')}</Th>
                  <Th>{t('vendor_detail.contract_type')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th>{t('vendor_detail.start_date')}</Th>
                  <Th>{t('vendor_detail.end_date')}</Th>
                  <Th>{t('vendor_detail.annual_value')}</Th>
                  {isAdmin && <th className="px-4 py-2 text-right font-medium text-foreground">{t('table.actions')}</th>}
                </tr>
              </thead>
              <tbody>
                {contracts.map((c) => (
                  <tr key={c.id}>
                    <Td className="font-medium">{c.title}</Td>
                    <Td><Badge variant="info">{t(`vendor_detail.type_${c.contract_type}`)}</Badge></Td>
                    <Td><Badge variant={STATUS_VARIANT[c.status] ?? 'default'}>{c.status}</Badge></Td>
                    <Td>{formatDate(c.start_date)}</Td>
                    <Td>{c.end_date ? formatDate(c.end_date) : '—'}</Td>
                    <Td>{c.annual_value != null ? `${c.currency || '€'} ${Number(c.annual_value).toLocaleString()}` : '—'}</Td>
                    {isAdmin && (
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-1">
                          <button onClick={() => openEdit(c)} className="text-xs px-2 py-1 rounded border hover:bg-secondary">{t('common.edit')}</button>
                          {c.status === 'draft' && (
                            <button onClick={() => changeStatusMut.mutate({ contractId: c.id, status: 'active' })} className="text-xs px-2 py-1 rounded border border-green-200 text-green-700 hover:bg-green-50">{t('vendor_detail.activate')}</button>
                          )}
                          {c.status === 'active' && (
                            <button onClick={() => changeStatusMut.mutate({ contractId: c.id, status: 'terminated' })} className="text-xs px-2 py-1 rounded border border-red-200 text-red-700 hover:bg-red-50">{t('vendor_detail.terminate')}</button>
                          )}
                          <button onClick={() => setPendingDelete(c.id)} className="text-xs px-2 py-1 rounded border border-destructive/20 text-destructive hover:bg-destructive/10">{t('common.delete')}</button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={page} pageSize={pageSize} total={total} onChange={setPage} />
          </>
        )}
      </Card>

      {/* Contract Form Modal */}
      {showForm && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button type="button" className="absolute inset-0 bg-black/40" onClick={resetForm} aria-label="Close" />
          <div className="relative z-[91] w-full max-w-2xl rounded-xl border border-border bg-card p-6 shadow-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">{editId ? t('vendor_detail.edit_contract') : t('vendor_detail.new_contract')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); saveMut.mutate(); }} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block mb-1.5 text-sm text-muted-foreground">{t('vendor_detail.contract_title')}</label>
                  <input value={title} onChange={(e) => setTitle(e.target.value)} required className="w-full bg-card" />
                </div>
                <div>
                  <label className="block mb-1.5 text-sm text-muted-foreground">{t('vendor_detail.contract_type')}</label>
                  <select value={contractType} onChange={(e) => setContractType(e.target.value)} className="w-full bg-card">
                    {['service', 'license', 'support', 'consulting', 'hosting', 'other'].map((v) => (
                      <option key={v} value={v}>{t(`vendor_detail.type_${v}`)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block mb-1.5 text-sm text-muted-foreground">{t('vendor_detail.start_date')}</label>
                  <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required className="w-full bg-card" />
                </div>
                <div>
                  <label className="block mb-1.5 text-sm text-muted-foreground">{t('vendor_detail.end_date')}</label>
                  <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-full bg-card" />
                </div>
                <div>
                  <label className="block mb-1.5 text-sm text-muted-foreground">{t('vendor_detail.annual_value')}</label>
                  <input type="number" value={annualValue} onChange={(e) => setAnnualValue(e.target.value)} min="0" step="0.01" className="w-full bg-card" />
                </div>
                <div>
                  <label className="block mb-1.5 text-sm text-muted-foreground">{t('vendor_detail.currency')}</label>
                  <select value={currency} onChange={(e) => setCurrency(e.target.value)} className="w-full bg-card">
                    {['EUR', 'USD', 'GBP'].map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block mb-1.5 text-sm text-muted-foreground">{t('vendor_detail.renewal_date')}</label>
                <input type="date" value={renewalDate} onChange={(e) => setRenewalDate(e.target.value)} className="w-full bg-card" />
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="auto_renewal" checked={autoRenewal} onChange={(e) => setAutoRenewal(e.target.checked)} className="h-4 w-4 rounded border-input" />
                <label htmlFor="auto_renewal" className="text-sm text-muted-foreground">{t('vendor_detail.auto_renewal')}</label>
              </div>

              {/* Security Clauses */}
              <div>
                <h4 className="text-sm font-medium text-foreground mb-2">{t('vendor_detail.security_clauses')}</h4>
                <div className="grid grid-cols-1 gap-2">
                  {Object.keys(securityClauses).map((key) => (
                    <div key={key} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id={`clause_${key}`}
                        checked={securityClauses[key] ?? false}
                        onChange={(e) => setSecurityClauses((prev) => ({ ...prev, [key]: e.target.checked }))}
                        className="h-4 w-4 rounded border-input"
                      />
                      <label htmlFor={`clause_${key}`} className="text-sm text-muted-foreground">{t(`vendor_detail.clause_${key}`)}</label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block mb-1.5 text-sm text-muted-foreground">{t('page.vendors.notes')}</label>
                <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} className="w-full bg-card" />
              </div>

              <div className="flex justify-end gap-2">
                <button type="button" onClick={resetForm} className="h-9 px-4 text-sm rounded-md border hover:bg-secondary">{t('common.cancel')}</button>
                <button type="submit" disabled={saveMut.isPending} className="h-9 px-4 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                  {saveMut.isPending ? t('common.working') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={t('vendor_detail.confirm_delete_contract')}
        description={t('vendor_detail.confirm_delete_contract_desc')}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={deleteMut.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => { if (pendingDelete) deleteMut.mutate(pendingDelete); }}
      />
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// Assessments Tab
// ═══════════════════════════════════════════════════════
function AssessmentsTab({ vendorId, isAdmin, t, queryClient, showToast }: {
  vendorId: string; isAdmin: boolean; t: (k: string) => string;
  queryClient: ReturnType<typeof useQueryClient>; showToast: (o: { title: string; variant?: string }) => void;
}) {
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [scores, setScores] = useState({ data_handling: 3, security_certs: 3, incident_response: 3, business_continuity: 3, subcontractor: 3 });
  const [justification, setJustification] = useState('');
  const [nextReviewDate, setNextReviewDate] = useState('');
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const pageSize = 10;

  const { data, isLoading } = useQuery({
    queryKey: ['vendor-assessments', vendorId, page],
    queryFn: async () => {
      const { data } = await api.get(`/vendors/${vendorId}/assessments?page=${page}&page_size=${pageSize}`);
      return data as PaginatedResponse<VendorRiskAssessment>;
    },
  });

  const assessments = data?.data ?? [];
  const total = data?.meta?.total ?? 0;

  const createMut = useMutation({
    mutationFn: async () => {
      await api.post(`/vendors/${vendorId}/assessments`, {
        assessment_date: new Date().toISOString().split('T')[0],
        data_handling_score: scores.data_handling,
        security_certs_score: scores.security_certs,
        incident_response_score: scores.incident_response,
        business_continuity_score: scores.business_continuity,
        subcontractor_score: scores.subcontractor,
        justification: justification || null,
        next_review_date: nextReviewDate || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-assessments', vendorId] });
      queryClient.invalidateQueries({ queryKey: ['vendor-risk-profile', vendorId] });
      setShowForm(false);
      setScores({ data_handling: 3, security_certs: 3, incident_response: 3, business_continuity: 3, subcontractor: 3 });
      setJustification(''); setNextReviewDate('');
      showToast({ title: t('vendor_detail.assessment_created'), variant: 'success' });
    },
  });

  const deleteMut = useMutation({
    mutationFn: async (assessmentId: string) => {
      await api.delete(`/vendors/${vendorId}/assessments/${assessmentId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-assessments', vendorId] });
      queryClient.invalidateQueries({ queryKey: ['vendor-risk-profile', vendorId] });
      setPendingDelete(null);
      showToast({ title: t('vendor_detail.assessment_deleted'), variant: 'success' });
    },
  });

  // Preview risk level
  const scoreValues = Object.values(scores);
  const avg = scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length;
  const previewLevel = avg <= 2 ? 'low' : avg <= 3 ? 'medium' : avg <= 4 ? 'high' : 'critical';

  return (
    <div>
      {isAdmin && (
        <div className="mb-4 flex justify-end">
          <button onClick={() => setShowForm(true)} className="inline-flex items-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs hover:bg-primary/90">
            {t('vendor_detail.new_assessment')}
          </button>
        </div>
      )}

      <Card>
        {isLoading ? <Loading /> : !assessments.length ? <EmptyState message={t('vendor_detail.no_assessments')} /> : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>{t('vendor_detail.assessment_date')}</Th>
                  <Th>{t('vendor_detail.risk_level')}</Th>
                  <Th>{t('vendor_detail.score_data_handling')}</Th>
                  <Th>{t('vendor_detail.score_security_certs')}</Th>
                  <Th>{t('vendor_detail.score_incident_response')}</Th>
                  <Th>{t('vendor_detail.score_business_continuity')}</Th>
                  <Th>{t('vendor_detail.score_subcontractor')}</Th>
                  {isAdmin && <th className="px-4 py-2 text-right font-medium">{t('table.actions')}</th>}
                </tr>
              </thead>
              <tbody>
                {assessments.map((a, i) => (
                  <tr key={a.id} className={i === 0 ? 'bg-primary/5' : ''}>
                    <Td>{formatDate(a.assessment_date)}{i === 0 && <Badge variant="info" className="ml-2 text-[10px]">{t('vendor_detail.latest')}</Badge>}</Td>
                    <Td><Badge variant={RISK_VARIANT[a.overall_risk_level] ?? 'info'}>{a.overall_risk_level}</Badge></Td>
                    <Td>{a.data_handling_score}</Td>
                    <Td>{a.security_certs_score}</Td>
                    <Td>{a.incident_response_score}</Td>
                    <Td>{a.business_continuity_score}</Td>
                    <Td>{a.subcontractor_score}</Td>
                    {isAdmin && (
                      <td className="px-4 py-3 text-right">
                        <button onClick={() => setPendingDelete(a.id)} className="text-xs px-2 py-1 rounded border border-destructive/20 text-destructive hover:bg-destructive/10">{t('common.delete')}</button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={page} pageSize={pageSize} total={total} onChange={setPage} />
          </>
        )}
      </Card>

      {/* Assessment Form Modal */}
      {showForm && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button type="button" className="absolute inset-0 bg-black/40" onClick={() => setShowForm(false)} aria-label="Close" />
          <div className="relative z-[91] w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold mb-4">{t('vendor_detail.new_assessment')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); createMut.mutate(); }} className="space-y-4">
              {(['data_handling', 'security_certs', 'incident_response', 'business_continuity', 'subcontractor'] as const).map((key) => (
                <div key={key}>
                  <label className="block mb-1 text-sm text-muted-foreground">{t(`vendor_detail.score_${key}`)}</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range" min="1" max="5" value={scores[key]}
                      onChange={(e) => setScores((prev) => ({ ...prev, [key]: Number(e.target.value) }))}
                      className="flex-1"
                    />
                    <span className="w-6 text-sm font-medium text-center">{scores[key]}</span>
                  </div>
                </div>
              ))}
              <div className="flex items-center gap-2 p-3 rounded-lg bg-muted">
                <span className="text-sm text-muted-foreground">{t('vendor_detail.preview_risk')}:</span>
                <Badge variant={RISK_VARIANT[previewLevel] ?? 'info'}>{previewLevel}</Badge>
              </div>
              <div>
                <label className="block mb-1 text-sm text-muted-foreground">{t('vendor_detail.justification')}</label>
                <textarea value={justification} onChange={(e) => setJustification(e.target.value)} rows={2} className="w-full bg-card" />
              </div>
              <div>
                <label className="block mb-1 text-sm text-muted-foreground">{t('vendor_detail.next_review')}</label>
                <input type="date" value={nextReviewDate} onChange={(e) => setNextReviewDate(e.target.value)} className="w-full bg-card" />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setShowForm(false)} className="h-9 px-4 text-sm rounded-md border hover:bg-secondary">{t('common.cancel')}</button>
                <button type="submit" disabled={createMut.isPending} className="h-9 px-4 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                  {createMut.isPending ? t('common.working') : t('vendor_detail.submit_assessment')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={t('vendor_detail.confirm_delete_assessment')}
        description={t('vendor_detail.confirm_delete_assessment_desc')}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={deleteMut.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => { if (pendingDelete) deleteMut.mutate(pendingDelete); }}
      />
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// Dependencies Tab
// ═══════════════════════════════════════════════════════
function DependenciesTab({ vendorId, isAdmin, t, queryClient, showToast }: {
  vendorId: string; isAdmin: boolean; t: (k: string) => string;
  queryClient: ReturnType<typeof useQueryClient>; showToast: (o: { title: string; variant?: string }) => void;
}) {
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [description, setDescription] = useState('');
  const [businessFunction, setBusinessFunction] = useState('it_operations');
  const [isCritical, setIsCritical] = useState(false);
  const [notes, setNotes] = useState('');
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const pageSize = 10;

  const BF_OPTIONS = ['it_operations', 'security', 'communications', 'data_storage', 'cloud_infrastructure', 'software', 'hardware_supply', 'consulting', 'other'];

  const { data, isLoading } = useQuery({
    queryKey: ['vendor-dependencies', vendorId, page],
    queryFn: async () => {
      const { data } = await api.get(`/vendors/${vendorId}/dependencies?page=${page}&page_size=${pageSize}`);
      return data as PaginatedResponse<VendorDependency>;
    },
  });

  const deps = data?.data ?? [];
  const total = data?.meta?.total ?? 0;

  const resetForm = () => {
    setShowForm(false); setEditId(null); setDescription('');
    setBusinessFunction('it_operations'); setIsCritical(false); setNotes('');
  };

  const openEdit = (d: VendorDependency) => {
    setEditId(d.id); setDescription(d.service_description);
    setBusinessFunction(d.business_function); setIsCritical(d.is_critical);
    setNotes(d.notes || ''); setShowForm(true);
  };

  const saveMut = useMutation({
    mutationFn: async () => {
      const payload = {
        service_description: description,
        business_function: businessFunction,
        is_critical: isCritical,
        notes: notes || null,
      };
      if (editId) {
        await api.put(`/vendors/${vendorId}/dependencies/${editId}`, payload);
      } else {
        await api.post(`/vendors/${vendorId}/dependencies`, payload);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-dependencies', vendorId] });
      queryClient.invalidateQueries({ queryKey: ['vendor-risk-profile', vendorId] });
      resetForm();
      showToast({ title: editId ? t('vendor_detail.dependency_updated') : t('vendor_detail.dependency_created'), variant: 'success' });
    },
  });

  const deleteMut = useMutation({
    mutationFn: async (depId: string) => {
      await api.delete(`/vendors/${vendorId}/dependencies/${depId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-dependencies', vendorId] });
      queryClient.invalidateQueries({ queryKey: ['vendor-risk-profile', vendorId] });
      setPendingDelete(null);
      showToast({ title: t('vendor_detail.dependency_deleted'), variant: 'success' });
    },
  });

  return (
    <div>
      {isAdmin && (
        <div className="mb-4 flex justify-end">
          <button onClick={() => { resetForm(); setShowForm(true); }} className="inline-flex items-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs hover:bg-primary/90">
            {t('vendor_detail.add_dependency')}
          </button>
        </div>
      )}

      <Card>
        {isLoading ? <Loading /> : !deps.length ? <EmptyState message={t('vendor_detail.no_dependencies')} /> : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>{t('vendor_detail.service_description')}</Th>
                  <Th>{t('vendor_detail.business_function')}</Th>
                  <Th>{t('vendor_detail.criticality')}</Th>
                  {isAdmin && <th className="px-4 py-2 text-right font-medium">{t('table.actions')}</th>}
                </tr>
              </thead>
              <tbody>
                {deps.map((d) => (
                  <tr key={d.id}>
                    <Td>{d.service_description}</Td>
                    <Td><Badge variant="info">{t(`dependencies.bf_${d.business_function}`)}</Badge></Td>
                    <Td>
                      {d.is_critical ? (
                        <Badge variant="danger"><Shield className="h-3 w-3 mr-1" />{t('vendor_detail.critical')}</Badge>
                      ) : (
                        <Badge variant="default">{t('vendor_detail.non_critical')}</Badge>
                      )}
                    </Td>
                    {isAdmin && (
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-1">
                          <button onClick={() => openEdit(d)} className="text-xs px-2 py-1 rounded border hover:bg-secondary">{t('common.edit')}</button>
                          <button onClick={() => setPendingDelete(d.id)} className="text-xs px-2 py-1 rounded border border-destructive/20 text-destructive hover:bg-destructive/10">{t('common.delete')}</button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={page} pageSize={pageSize} total={total} onChange={setPage} />
          </>
        )}
      </Card>

      {showForm && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button type="button" className="absolute inset-0 bg-black/40" onClick={resetForm} aria-label="Close" />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold mb-4">{editId ? t('vendor_detail.edit_dependency') : t('vendor_detail.new_dependency')}</h3>
            <form onSubmit={(e) => { e.preventDefault(); saveMut.mutate(); }} className="space-y-4">
              <div>
                <label className="block mb-1.5 text-sm text-muted-foreground">{t('vendor_detail.service_description')}</label>
                <input value={description} onChange={(e) => setDescription(e.target.value)} required className="w-full bg-card" />
              </div>
              <div>
                <label className="block mb-1.5 text-sm text-muted-foreground">{t('vendor_detail.business_function')}</label>
                <select value={businessFunction} onChange={(e) => setBusinessFunction(e.target.value)} className="w-full bg-card">
                  {BF_OPTIONS.map((v) => <option key={v} value={v}>{t(`dependencies.bf_${v}`)}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="is_critical" checked={isCritical} onChange={(e) => setIsCritical(e.target.checked)} className="h-4 w-4 rounded border-input" />
                <label htmlFor="is_critical" className="text-sm text-muted-foreground">{t('vendor_detail.mark_critical')}</label>
              </div>
              <div>
                <label className="block mb-1.5 text-sm text-muted-foreground">{t('page.vendors.notes')}</label>
                <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} className="w-full bg-card" />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={resetForm} className="h-9 px-4 text-sm rounded-md border hover:bg-secondary">{t('common.cancel')}</button>
                <button type="submit" disabled={saveMut.isPending} className="h-9 px-4 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                  {saveMut.isPending ? t('common.working') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={t('vendor_detail.confirm_delete_dependency')}
        description={t('vendor_detail.confirm_delete_dependency_desc')}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={deleteMut.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => { if (pendingDelete) deleteMut.mutate(pendingDelete); }}
      />
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// Incidents Tab (read-only)
// ═══════════════════════════════════════════════════════
function IncidentsTab({ profile, t }: { profile: VendorRiskProfile; t: (k: string) => string }) {
  if (!profile.incidents.length) return <Card className="p-6"><EmptyState message={t('vendor_detail.no_incidents')} /></Card>;
  return (
    <Card>
      <Table>
        <thead>
          <tr>
            <Th>{t('vendor_detail.incident_title')}</Th>
            <Th>{t('vendor_detail.severity')}</Th>
            <Th>{t('table.status')}</Th>
            <Th>{t('vendor_detail.date')}</Th>
          </tr>
        </thead>
        <tbody>
          {profile.incidents.map((inc) => (
            <tr key={inc.id}>
              <Td>
                <Link to={`/incidents/${inc.id}`} className="text-primary hover:underline">{inc.title}</Link>
              </Td>
              <Td><Badge variant={SEVERITY_VARIANT[inc.severity] ?? 'default'}>{inc.severity}</Badge></Td>
              <Td><Badge variant="info">{inc.status}</Badge></Td>
              <Td>{inc.created_at ? formatDateTime(inc.created_at) : '—'}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════
// Risks Tab (read-only)
// ═══════════════════════════════════════════════════════
function RisksTab({ profile, t }: { profile: VendorRiskProfile; t: (k: string) => string }) {
  if (!profile.risks.length) return <Card className="p-6"><EmptyState message={t('vendor_detail.no_risks')} /></Card>;
  return (
    <Card>
      <Table>
        <thead>
          <tr>
            <Th>{t('vendor_detail.risk_title')}</Th>
            <Th>{t('vendor_detail.risk_level')}</Th>
            <Th>{t('table.status')}</Th>
          </tr>
        </thead>
        <tbody>
          {profile.risks.map((r) => (
            <tr key={r.id}>
              <Td>
                <Link to={`/risks/${r.id}`} className="text-primary hover:underline">{r.title}</Link>
              </Td>
              <Td>{r.risk_level ? <Badge variant={RISK_VARIANT[r.risk_level] ?? 'info'}>{r.risk_level}</Badge> : '—'}</Td>
              <Td><Badge variant="info">{r.status}</Badge></Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}
