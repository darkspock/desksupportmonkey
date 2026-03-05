import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2, ChevronLeft, ChevronRight, Plus, Copy, Check, X } from 'lucide-react';
import { useResellerAuth } from '../../contexts/ResellerAuthContext';
import { useI18n } from '../../lib/i18n';
import api from '../../lib/api';
import { cn } from '../../lib/cn';

interface ResellerClient {
  id: string;
  reseller_id: string;
  company_id: string;
  company_name: string;
  source: string;
  is_demo: boolean;
  demo_expires_at: string | null;
  plan: string;
  company_status: string;
  created_at: string | null;
}

interface ClientListResponse {
  items: ResellerClient[];
  total: number;
}

function formatDate(iso: string | null): string {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString();
}

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  suspended: 'bg-yellow-100 text-yellow-800',
  deactivated: 'bg-red-100 text-red-800',
};

interface DemoCreatedResult {
  company_name: string;
  admin_email: string;
  admin_password: string;
}

function CreateDemoModal({
  open,
  onClose,
  token,
}: {
  open: boolean;
  onClose: (created: boolean) => void;
  token: string;
}) {
  const { t } = useI18n();
  const [companyName, setCompanyName] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<DemoCreatedResult | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const payload: Record<string, string> = { company_name: companyName };
      if (adminEmail.trim()) payload.admin_email = adminEmail.trim();
      const { data } = await api.post<{ data: DemoCreatedResult }>(
        '/reseller/clients/demo',
        payload,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setResult(data.data);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    const created = result !== null;
    setCompanyName('');
    setAdminEmail('');
    setError('');
    setResult(null);
    onClose(created);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={handleClose}>
      <div
        className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-foreground">{t('reseller.demo.modal_title')}</h2>
          <button type="button" onClick={handleClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        {result ? (
          <div className="space-y-4">
            <div className="rounded-lg border border-green-200 bg-green-50 p-3">
              <p className="text-sm font-medium text-green-800">{t('reseller.demo.created_success')}</p>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{t('reseller.demo.company')}</p>
                <p className="mt-0.5 text-sm text-foreground">{result.company_name}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{t('reseller.demo.admin_email')}</p>
                <div className="mt-0.5 flex items-center gap-2">
                  <code className="text-sm bg-secondary px-2 py-0.5 rounded">{result.admin_email}</code>
                  <button type="button" onClick={() => copyToClipboard(result.admin_email, 'email')} className="text-muted-foreground hover:text-foreground">
                    {copiedField === 'email' ? <Check className="h-3.5 w-3.5 text-green-600" /> : <Copy className="h-3.5 w-3.5" />}
                  </button>
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{t('reseller.demo.admin_password')}</p>
                <div className="mt-0.5 flex items-center gap-2">
                  <code className="text-sm bg-secondary px-2 py-0.5 rounded">{result.admin_password}</code>
                  <button type="button" onClick={() => copyToClipboard(result.admin_password, 'password')} className="text-muted-foreground hover:text-foreground">
                    {copiedField === 'password' ? <Check className="h-3.5 w-3.5 text-green-600" /> : <Copy className="h-3.5 w-3.5" />}
                  </button>
                </div>
              </div>
            </div>

            <p className="text-xs text-muted-foreground">{t('reseller.demo.credentials_warning')}</p>

            <button
              type="button"
              onClick={handleClose}
              className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90"
            >
              {t('common.close')}
            </button>
          </div>
        ) : (
          <form onSubmit={handleCreate} className="space-y-4">
            <p className="text-sm text-muted-foreground">{t('reseller.demo.modal_description')}</p>

            {error && (
              <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}

            <div>
              <label htmlFor="demo-company" className="block mb-1.5 text-sm text-muted-foreground">
                {t('reseller.demo.company_name_label')}
              </label>
              <input
                id="demo-company"
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
                minLength={2}
                maxLength={200}
                className="w-full"
                placeholder={t('reseller.demo.company_name_placeholder')}
              />
            </div>

            <div>
              <label htmlFor="demo-email" className="block mb-1.5 text-sm text-muted-foreground">
                {t('reseller.demo.admin_email_label')}
              </label>
              <input
                id="demo-email"
                type="email"
                value={adminEmail}
                onChange={(e) => setAdminEmail(e.target.value)}
                className="w-full"
                placeholder={t('reseller.demo.admin_email_placeholder')}
              />
              <p className="mt-1 text-xs text-muted-foreground">{t('reseller.demo.admin_email_hint')}</p>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary"
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                disabled={loading || companyName.trim().length < 2}
                className="flex-1 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
              >
                {loading ? t('common.working') : t('reseller.demo.create_button')}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

const PAGE_SIZE = 20;

export default function ClientsPage() {
  const { token } = useResellerAuth();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [showDemoModal, setShowDemoModal] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['reseller-clients', offset],
    queryFn: async () => {
      const { data } = await api.get<{ data: ClientListResponse }>(
        `/reseller/clients?offset=${offset}&limit=${PAGE_SIZE}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      return data.data;
    },
    enabled: !!token,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-sm text-destructive">
        {t('common.error')}
      </div>
    );
  }

  const totalPages = Math.ceil(data.total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">{t('reseller.clients.title')}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t('reseller.clients.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={() => setShowDemoModal(true)}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          {t('reseller.demo.create_demo')}
        </button>
      </div>

      <CreateDemoModal
        open={showDemoModal}
        onClose={(created) => {
          setShowDemoModal(false);
          if (created) queryClient.invalidateQueries({ queryKey: ['reseller-clients'] });
        }}
        token={token!}
      />

      {data.items.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-6 text-center">
          <p className="text-sm text-muted-foreground">{t('reseller.clients.empty')}</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border bg-card">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-secondary/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.clients.col_company')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.clients.col_plan')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.clients.col_source')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.clients.col_status')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {t('reseller.clients.col_created')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((c) => (
                  <tr key={c.id}>
                    <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-foreground">
                      {c.company_name}
                      {c.is_demo && (
                        <span className="ml-1.5 inline-flex rounded bg-violet-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-violet-700">
                          Demo
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm capitalize text-muted-foreground">
                      {c.plan}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm capitalize text-muted-foreground">
                      {c.source}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <span className={cn(
                        'inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase',
                        statusColors[c.company_status] ?? 'bg-gray-100 text-gray-800',
                      )}>
                        {c.company_status}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                      {formatDate(c.created_at)}
                      {c.is_demo && c.demo_expires_at && (
                        <span className="ml-1 text-xs text-muted-foreground/60">
                          (exp. {formatDate(c.demo_expires_at)})
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {data.total} {data.total === 1 ? 'client' : 'clients'}
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                  className="inline-flex items-center rounded-md border border-border px-2 py-1 text-sm disabled:opacity-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm text-muted-foreground">
                  {currentPage} / {totalPages}
                </span>
                <button
                  type="button"
                  disabled={offset + PAGE_SIZE >= data.total}
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                  className="inline-flex items-center rounded-md border border-border px-2 py-1 text-sm disabled:opacity-50"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
