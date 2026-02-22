import { useEffect, useRef, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';

interface BillingOverview {
  billing_status: string;
  plan: string;
}

const POLL_INTERVAL_MS = 2000;
const TIMEOUT_MS = 60000;

export default function BillingProcessingPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [timedOut, setTimedOut] = useState(false);
  const startRef = useRef<number>(Date.now());
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const poll = async () => {
      if (Date.now() - startRef.current >= TIMEOUT_MS) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        setTimedOut(true);
        return;
      }

      try {
        const { data } = await api.get<BillingOverview>('/billing/');
        if (data.billing_status === 'active') {
          if (intervalRef.current) clearInterval(intervalRef.current);
          // Invalidate so BillingPage re-fetches fresh data
          await queryClient.invalidateQueries({ queryKey: ['billing-overview'] });
          navigate('/billing', { replace: true });
        }
      } catch {
        // Swallow errors and keep polling
      }
    };

    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
    // Run first poll immediately
    poll();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [navigate, queryClient]);

  if (timedOut) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 text-center">
        <p className="text-sm text-muted-foreground max-w-sm">
          {t('page.billing.processing.timeout')}
        </p>
        <Link
          to="/billing"
          className="text-sm font-medium text-primary hover:underline"
        >
          {t('page.billing.processing.back')}
        </Link>
      </div>
    );
  }

  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 text-center">
      {/* Spinner */}
      <svg
        className="h-10 w-10 animate-spin text-primary"
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      <h2 className="text-lg font-semibold text-foreground">
        {t('page.billing.processing.title')}
      </h2>
      <p className="text-sm text-muted-foreground max-w-sm">
        {t('page.billing.processing.desc')}
      </p>
    </div>
  );
}
