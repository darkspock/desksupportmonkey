import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { useI18n } from '../../lib/i18n';

interface AuthShellProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  showBackToLogin?: boolean;
}

export function AuthShell({ title, subtitle, children, showBackToLogin = false }: AuthShellProps) {
  const { t } = useI18n();
  const metrics = [
    {
      value: '<2s',
      label: t('auth.brand_metric_realtime_label'),
      description: t('auth.brand_metric_realtime_desc'),
    },
    {
      value: '4',
      label: t('auth.brand_metric_roles_label'),
      description: t('auth.brand_metric_roles_desc'),
    },
    {
      value: '24/7',
      label: t('auth.brand_metric_uptime_label'),
      description: t('auth.brand_metric_uptime_desc'),
    },
  ];

  return (
    <div className="auth-shell-bg min-h-screen">
      <div className="mx-auto grid min-h-screen max-w-[1240px] grid-cols-1 gap-6 px-4 py-5 md:px-8 md:py-8 lg:grid-cols-[1.08fr_0.92fr] lg:gap-10 lg:px-10">
        <section className="relative hidden overflow-hidden rounded-[30px] border border-slate-700/60 bg-slate-950 p-8 text-white lg:flex lg:flex-col">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(120%_120%_at_0%_0%,rgba(59,130,246,0.2)_0%,rgba(15,23,42,0)_58%),radial-gradient(130%_130%_at_100%_100%,rgba(14,165,233,0.18)_0%,rgba(2,6,23,0)_62%)]" />
          <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_bottom,rgba(148,163,184,0.1)_1px,transparent_1px)] [background-size:100%_26px] opacity-25" />

          <div className="relative flex h-full flex-col">
            <div className="flex items-center gap-3">
              <img
                src="/logo.png"
                alt="DeskSupportMonkey"
                className="h-11 w-11 rounded-xl border border-white/20 bg-slate-900/80 p-1"
              />
              <div className="space-y-0.5">
                <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-100">DeskSupportMonkey</p>
                <p className="text-xs text-slate-300">{t('auth.brand_caption')}</p>
              </div>
            </div>

            <div className="mt-10 max-w-xl">
              <h2 className="text-balance text-4xl font-semibold leading-tight [font-family:var(--dsm-font-display)]">
                {t('auth.brand_tagline')}
              </h2>
              <p className="mt-5 text-base leading-relaxed text-slate-300">
                {t('auth.brand_subtitle')}
              </p>
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              {metrics.map((metric) => (
                <div key={metric.label} className="rounded-2xl border border-white/15 bg-white/5 p-4 backdrop-blur-sm">
                  <p className="text-2xl font-semibold text-white">{metric.value}</p>
                  <p className="mt-1 text-xs font-semibold uppercase tracking-[0.12em] text-slate-300">{metric.label}</p>
                  <p className="mt-2 text-xs leading-relaxed text-slate-300">{metric.description}</p>
                </div>
              ))}
            </div>

            <div className="mt-auto rounded-2xl border border-white/15 bg-slate-900/70 p-5 backdrop-blur-sm">
              <div className="flex items-center gap-4">
                <img
                  src="/logo.png"
                  alt="DeskSupportMonkey mascot"
                  className="auth-float h-20 w-auto shrink-0 drop-shadow-[0_8px_18px_rgba(15,23,42,0.55)]"
                />
                <div>
                  <p className="text-sm font-semibold text-slate-100">{t('auth.brand_card_title')}</p>
                  <p className="mt-1 text-sm leading-relaxed text-slate-300">{t('auth.brand_card_desc')}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center py-4 lg:py-0">
          <div className="auth-fade-up w-full max-w-xl rounded-[28px] border border-slate-200/85 bg-white/95 p-6 shadow-[0_22px_70px_-36px_rgba(15,23,42,0.45)] backdrop-blur sm:p-8">
            <div className="mb-6 flex items-center gap-3 lg:hidden">
              <img src="/logo.png" alt="DeskSupportMonkey" className="h-10 w-10" />
              <p className="text-sm font-semibold text-slate-700">DeskSupportMonkey</p>
            </div>
            <p className="inline-flex rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-blue-700">
              {t('auth.secure_access')}
            </p>
            <h1 className="mt-4 text-3xl font-semibold text-slate-900 [font-family:var(--dsm-font-display)]">{title}</h1>
            <p className="mt-2 text-base text-slate-600">{subtitle}</p>
            <div className="mt-7">{children}</div>
            {showBackToLogin && (
              <p className="mt-8 text-center text-xs text-slate-500">
                {t('auth.help')}{' '}
                <Link to="/auth/login" className="text-blue-700 hover:underline">{t('auth.back_to_login')}</Link>
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
