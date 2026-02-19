import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../hooks/useNotifications';
import { useI18n } from '../../lib/i18n';

interface HeaderProps {
  onMenuToggle?: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { user, logout } = useAuth();
  const { unread } = useNotifications();
  const { language, setLanguage, t } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const companyName = user?.company_name?.trim();
  const canManagePassword = user?.role === 'admin' || user?.role === 'super_admin';

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const initials = user?.email
    ? user.email.substring(0, 2).toUpperCase()
    : '??';

  return (
    <header className="sticky top-0 z-30 h-14 border-b border-border bg-card flex items-center justify-between px-4 md:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuToggle}
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border text-muted-foreground hover:bg-accent md:hidden"
          aria-label={t('header.open_navigation')}
          title={t('header.open_navigation')}
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <p className="text-sm font-semibold text-foreground md:hidden">DeskSupportMonkey</p>
        {companyName && (
          <div className="hidden max-w-[280px] items-center gap-2 rounded-md border border-border bg-secondary px-3 py-1.5 md:flex">
            <svg className="h-4 w-4 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21h18M5 21V7a2 2 0 012-2h10a2 2 0 012 2v14M9 9h1m4 0h1M9 13h1m4 0h1M9 17h1m4 0h1" />
            </svg>
            <p className="truncate text-xs font-semibold text-secondary-foreground" title={companyName}>{companyName}</p>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <label className="sr-only" htmlFor="language-selector">{t('header.language')}</label>
        <select
          id="language-selector"
          value={language}
          onChange={(e) => setLanguage(e.target.value as 'en' | 'es')}
          className="rounded-md border border-input bg-card px-2 py-1 text-xs text-foreground"
          aria-label={t('header.language')}
        >
          <option value="en">EN</option>
          <option value="es">ES</option>
        </select>

        <Link to="/my/notifications" className="relative text-muted-foreground hover:text-foreground transition-colors" aria-label={t('header.notifications')} title={t('header.notifications')}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          {unread > 0 && (
            <span className="absolute -top-1 -right-1 bg-destructive text-primary-foreground text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </Link>

        <div className="relative" ref={ref}>
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="flex items-center gap-2"
            aria-haspopup="menu"
            aria-expanded={open}
          >
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-xs font-medium text-primary">{initials}</span>
            </div>
            <div className="hidden md:flex flex-col text-left">
              <span className="text-sm font-medium text-foreground leading-none max-w-[140px] truncate">{user?.email}</span>
              <span className="text-[11px] text-muted-foreground leading-none mt-0.5">{t(`enum.${user?.role ?? ''}`)}</span>
            </div>
          </button>
          {open && (
            <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-lg shadow-lg py-1 z-50">
              {companyName && (
                <div className="truncate border-b border-border px-3 py-2 text-sm text-foreground">{companyName}</div>
              )}
              <div className="px-3 py-2 text-xs text-muted-foreground border-b border-border">{t(`enum.${user?.role ?? ''}`)}</div>
              {canManagePassword && (
                <Link
                  to="/auth/change-password"
                  onClick={() => setOpen(false)}
                  className="block px-3 py-2 text-sm text-foreground hover:bg-accent"
                >
                  {t('header.change_password')}
                </Link>
              )}
              <button onClick={logout} className="w-full text-left px-3 py-2 text-sm text-destructive hover:bg-accent">
                {t('header.sign_out')}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
