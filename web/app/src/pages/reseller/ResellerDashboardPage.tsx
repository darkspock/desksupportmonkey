import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Copy, Check, Loader2 } from 'lucide-react';
import { useResellerAuth } from '../../contexts/ResellerAuthContext';
import { useI18n } from '../../lib/i18n';
import api from '../../lib/api';
import type { ResellerDashboard } from '../../types';

function formatCents(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

function ReferralLinkSection({ referralCode }: { referralCode: string }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const referralUrl = `${window.location.origin}/auth/register?ref=${referralCode}`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(referralUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h2 className="text-lg font-semibold text-foreground">{t('reseller.dashboard.referral_code')}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{t('reseller.dashboard.referral_desc')}</p>
      <div className="mt-3 flex items-center gap-2">
        <input
          type="text"
          readOnly
          value={referralUrl}
          className="flex-1 rounded-md border border-border bg-secondary px-3 py-2 text-sm font-mono text-foreground"
        />
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-2 text-sm font-medium text-foreground shadow-xs transition-colors hover:bg-secondary"
        >
          {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
          {copied ? t('common.copied') : t('common.copy')}
        </button>
      </div>
    </div>
  );
}

export default function ResellerDashboardPage() {
  const { reseller, token } = useResellerAuth();
  const { t } = useI18n();

  const { data, isLoading, isError } = useQuery({
    queryKey: ['reseller-dashboard'],
    queryFn: async () => {
      const { data } = await api.get<{ data: ResellerDashboard }>('/reseller/dashboard', {
        headers: { Authorization: `Bearer ${token}` },
      });
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

  const stats = [
    { label: t('reseller.dashboard.clients'), value: String(data.client_count) },
    { label: t('reseller.dashboard.total_commissions'), value: formatCents(data.total_commissions_cents) },
    { label: t('reseller.dashboard.available_balance'), value: formatCents(data.available_balance_cents) },
    { label: t('reseller.dashboard.pending_payout'), value: formatCents(data.pending_payout_cents) },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">
          {t('reseller.dashboard.title')}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {t('reseller.dashboard.welcome', { name: reseller?.name ?? '' })}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-lg border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">{stat.label}</p>
            <p className="mt-1 text-2xl font-semibold text-foreground">{stat.value}</p>
          </div>
        ))}
      </div>

      <ReferralLinkSection referralCode={data.referral_code} />

      {data.client_count === 0 && (
        <div className="rounded-lg border border-border bg-card p-6 text-center">
          <p className="text-sm text-muted-foreground">
            {t('reseller.dashboard.empty_state')}
          </p>
        </div>
      )}
    </div>
  );
}
