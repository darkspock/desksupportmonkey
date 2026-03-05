import { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../hooks/useNotifications';
import { useI18n } from '../../lib/i18n';
import { brand } from '../../config/brand';
import api from '../../lib/api';

interface HeaderProps {
  onMenuToggle?: () => void;
}

function resolveSectionKey(pathname: string): string | null {
  const sections: Array<{ key: string; prefixes: string[] }> = [
    { key: 'nav.section_my_tasks', prefixes: ['/my/tasks/', '/my/maintenance'] },
    { key: 'nav.section_my_activity', prefixes: ['/my/'] },
    {
      key: 'nav.section_operations',
      prefixes: ['/dashboard', '/requests', '/calendar', '/assets', '/vendors', '/purchase-orders', '/shipments', '/maintenance', '/addresses'],
    },
    { key: 'nav.section_knowledge', prefixes: ['/knowledge-base', '/kb', '/kb/categories'] },
    { key: 'nav.section_security', prefixes: ['/audit', '/incidents', '/risks', '/compliance'] },
    {
      key: 'nav.section_management',
      prefixes: ['/users', '/departments', '/reports', '/billing', '/settings/', '/maintenance-templates', '/sla/'],
    },
    { key: 'nav.section_platform', prefixes: ['/overview', '/companies', '/super-admin/'] },
  ];

  const match = sections.find((section) =>
    section.prefixes.some((prefix) => pathname.startsWith(prefix)),
  );
  return match?.key ?? null;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const location = useLocation();
  const { user, logout, refreshUser, companies, switchCompany } = useAuth();
  const { unread } = useNotifications();
  const { language, setLanguage, t } = useI18n();
  const [open, setOpen] = useState(false);
  const [nameModalOpen, setNameModalOpen] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [savingName, setSavingName] = useState(false);
  const [companyDropdownOpen, setCompanyDropdownOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const companyRef = useRef<HTMLDivElement>(null);
  const companyName = user?.company_name?.trim();
  const sectionKey = resolveSectionKey(location.pathname);
  const sectionLabel = sectionKey ? t(sectionKey) : null;
  const canManagePassword = user?.role === 'admin' || user?.role === 'super_admin';
  const isTech = user?.role === 'technician' || user?.role === 'admin' || user?.role === 'super_admin';

  const { data: queueCounts } = useQuery({
    queryKey: ['queue-counts'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/requests/queue-counts');
      return data.data as { urgent: number };
    },
    enabled: isTech,
    refetchInterval: 30_000,
  });

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
      if (companyRef.current && !companyRef.current.contains(e.target as Node)) setCompanyDropdownOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const initials = user?.email
    ? user.email.substring(0, 2).toUpperCase()
    : '??';

  const handleSwitch = async (companyId: string) => {
    if (switching) return;
    setSwitching(true);
    try {
      await switchCompany(companyId);
      window.location.href = '/';
    } finally {
      setSwitching(false);
    }
  };

  const openNameModal = () => {
    setNameInput(user?.name ?? '');
    setNameModalOpen(true);
    setOpen(false);
  };

  const handleSaveName = async () => {
    if (!nameInput.trim() || savingName) return;
    setSavingName(true);
    try {
      await api.patch('/my/profile', { name: nameInput.trim() });
      await refreshUser();
      setNameModalOpen(false);
    } finally {
      setSavingName(false);
    }
  };

  return (
    <>
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
        <p className="text-sm font-semibold text-foreground md:hidden">{brand.name}</p>
        {companyName && (
          <div className="hidden md:flex items-center gap-2" ref={companyRef}>
            {companies.length >= 2 ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => !switching && setCompanyDropdownOpen(!companyDropdownOpen)}
                  disabled={switching}
                  className="flex max-w-[280px] items-center gap-2 rounded-md border border-border bg-secondary px-3 py-1.5 hover:bg-accent transition-colors disabled:opacity-50"
                >
                  <svg className="h-4 w-4 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21h18M5 21V7a2 2 0 012-2h10a2 2 0 012 2v14M9 9h1m4 0h1M9 13h1m4 0h1M9 17h1m4 0h1" />
                  </svg>
                  <span className="truncate text-xs font-semibold text-secondary-foreground">
                    {switching ? t('header.switching') : companyName}
                  </span>
                  <svg className="h-3 w-3 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {companyDropdownOpen && !switching && (
                  <div className="absolute left-0 mt-1 w-64 bg-card border border-border rounded-lg shadow-lg py-1 z-50">
                    <div className="px-3 py-1.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                      {t('header.switch_company')}
                    </div>
                    {companies.map((c) => (
                      <button
                        key={c.company_id}
                        type="button"
                        onClick={() => {
                          if (!c.is_current) {
                            setCompanyDropdownOpen(false);
                            handleSwitch(c.company_id);
                          }
                        }}
                        disabled={c.is_current}
                        className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                          c.is_current
                            ? 'bg-primary/5 text-foreground cursor-default'
                            : 'text-foreground hover:bg-accent'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="truncate font-medium">{c.company_name}</span>
                          <div className="flex items-center gap-1.5 shrink-0">
                            <span className="text-[10px] text-muted-foreground">{t(`enum.${c.role}`)}</span>
                            {c.is_current && (
                              <span className="text-[10px] font-medium text-primary">{t('header.current_company')}</span>
                            )}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex max-w-[280px] items-center gap-2 rounded-md border border-border bg-secondary px-3 py-1.5">
                <svg className="h-4 w-4 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21h18M5 21V7a2 2 0 012-2h10a2 2 0 012 2v14M9 9h1m4 0h1M9 13h1m4 0h1M9 17h1m4 0h1" />
                </svg>
                <div className="flex min-w-0 items-center gap-1 text-xs font-semibold text-secondary-foreground">
                  <span className="truncate" title={companyName}>
                    {companyName}
                  </span>
                </div>
              </div>
            )}
            {sectionLabel && (
              <div className="flex items-center gap-1 text-xs font-semibold text-secondary-foreground">
                <span className="text-muted-foreground">/</span>
                <span className="truncate" title={sectionLabel}>
                  {sectionLabel}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {isTech && (
          <Link
            to="/requests"
            className="relative text-muted-foreground hover:text-foreground transition-colors"
            aria-label={t('header.request_queue', undefined, { defaultValue: 'Request Queue' })}
            title={t('header.request_queue', undefined, { defaultValue: 'Request Queue' })}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            {queueCounts && queueCounts.urgent > 0 && (
              <span className="absolute -top-1.5 -right-1.5 bg-destructive text-primary-foreground text-[9px] font-bold rounded-full min-w-[14px] h-3.5 px-0.5 flex items-center justify-center">
                {queueCounts.urgent > 9 ? '9+' : queueCounts.urgent}
              </span>
            )}
          </Link>
        )}
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
              <div className="px-3 py-2 border-b border-border">
                <div className="text-xs text-muted-foreground">{t(`enum.${user?.role ?? ''}`)}</div>
                {user?.name && <div className="truncate text-sm text-foreground mt-0.5">{user.name}</div>}
              </div>
              <div className="border-b border-border px-3 py-2">
                <div className="mb-1 text-xs text-muted-foreground">{t('header.language')}</div>
                <div role="group" aria-label={t('header.language')} className="inline-flex w-full items-center rounded-md border border-input bg-card p-0.5">
                  <button
                    type="button"
                    onClick={() => setLanguage('es')}
                    aria-pressed={language === 'es'}
                    className={`inline-flex h-7 flex-1 items-center justify-center rounded-sm px-2 text-xs font-medium transition-colors ${language === 'es' ? 'bg-primary text-primary-foreground' : 'text-foreground hover:bg-accent'}`}
                  >
                    ES
                  </button>
                  <button
                    type="button"
                    onClick={() => setLanguage('en')}
                    aria-pressed={language === 'en'}
                    className={`inline-flex h-7 flex-1 items-center justify-center rounded-sm px-2 text-xs font-medium transition-colors ${language === 'en' ? 'bg-primary text-primary-foreground' : 'text-foreground hover:bg-accent'}`}
                  >
                    EN
                  </button>
                </div>
              </div>
              <button
                type="button"
                onClick={openNameModal}
                className="w-full text-left px-3 py-2 text-sm text-foreground hover:bg-accent"
              >
                {t('header.change_name')}
              </button>
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

    {nameModalOpen && (
      <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
        <button
          type="button"
          className="absolute inset-0 bg-black/40"
          onClick={() => setNameModalOpen(false)}
          aria-label={t('common.close')}
        />
        <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
          <h3 className="text-lg font-semibold text-foreground">
            {t('header.change_name')}
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            {t('profile.enter_name')}
          </p>
          <input
            type="text"
            value={nameInput}
            onChange={(e) => setNameInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSaveName(); }}
            placeholder={t('profile.full_name')}
            autoFocus
            maxLength={100}
            className="mt-4 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <div className="mt-5 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setNameModalOpen(false)}
              disabled={savingName}
              className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
            >
              {t('common.cancel')}
            </button>
            <button
              type="button"
              onClick={handleSaveName}
              disabled={!nameInput.trim() || savingName}
              className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium shadow-xs transition-all disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {savingName ? t('common.saving') : t('common.save')}
            </button>
          </div>
        </div>
      </div>
    )}
    </>
  );
}
