import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { useI18n } from '../../lib/i18n';

interface AuthShellProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export function AuthShell({ title, subtitle, children }: AuthShellProps) {
  const { t } = useI18n();

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="mx-auto grid min-h-screen max-w-6xl grid-cols-1 gap-6 p-4 md:grid-cols-2 md:p-8">
        <section className="hidden rounded-2xl bg-slate-900 p-8 text-white md:flex md:flex-col md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-300">DeskSupportMonkey</p>
            <h2 className="mt-4 text-3xl font-bold leading-tight">{t('auth.brand_tagline')}</h2>
            <p className="mt-3 max-w-md text-sm text-slate-300">
              {t('auth.brand_subtitle')}
            </p>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-800/70 p-5">
            <img src="/logo.png" alt="DeskSupportMonkey" className="h-24 w-auto" />
          </div>
        </section>

        <section className="flex items-center justify-center">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <div className="mb-6 flex items-center gap-3 md:hidden">
              <img src="/logo.png" alt="DeskSupportMonkey" className="h-10 w-10" />
              <p className="text-sm font-semibold text-slate-700">DeskSupportMonkey</p>
            </div>
            <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
            <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
            <div className="mt-6">{children}</div>
            <p className="mt-8 text-center text-xs text-slate-500">
              {t('auth.help')}{' '}
              <Link to="/auth/login" className="text-blue-700 hover:underline">{t('auth.back_to_login')}</Link>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
