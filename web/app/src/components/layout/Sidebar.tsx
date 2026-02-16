import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '../../lib/cn';
import { useI18n } from '../../lib/i18n';

interface NavItem {
  to: string;
  labelKey: string;
  roles?: string[];
}

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

const nav: NavItem[] = [
  { to: '/my/equipment', labelKey: 'nav.my_equipment' },
  { to: '/my/requests', labelKey: 'nav.my_requests' },
  { to: '/requests', labelKey: 'nav.request_queue', roles: ['technician', 'admin', 'super_admin'] },
  { to: '/assets', labelKey: 'nav.asset_inventory', roles: ['technician', 'admin', 'super_admin'] },
  { to: '/dashboard', labelKey: 'nav.dashboard', roles: ['admin', 'super_admin'] },
  { to: '/users', labelKey: 'nav.users', roles: ['admin', 'super_admin'] },
  { to: '/departments', labelKey: 'nav.departments', roles: ['admin', 'super_admin'] },
  { to: '/reports', labelKey: 'nav.reports', roles: ['admin', 'super_admin'] },
  { to: '/companies', labelKey: 'nav.companies', roles: ['super_admin'] },
];

export function Sidebar({ mobileOpen = false, onClose }: SidebarProps) {
  const { user } = useAuth();
  const { t } = useI18n();
  const role = user?.role;
  const visible = nav.filter((item) => !item.roles || (role && item.roles.includes(role)));

  useEffect(() => {
    if (!mobileOpen) return;

    const onKeydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose?.();
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', onKeydown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', onKeydown);
    };
  }, [mobileOpen, onClose]);

  return (
    <>
      <aside className="hidden w-56 shrink-0 bg-gray-900 text-white min-h-screen md:flex md:flex-col">
        <div className="p-4 border-b border-gray-700 flex items-center gap-3">
          <img src="/logo.png" alt="DeskSupportMonkey" className="w-9 h-9 rounded" />
          <div>
            <h1 className="text-lg font-bold tracking-tight leading-tight">DSM</h1>
            <p className="text-xs text-gray-400">DeskSupportMonkey</p>
          </div>
        </div>
        <nav className="flex-1 p-2 space-y-0.5">
          {visible.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'block px-3 py-2 rounded text-sm transition-colors',
                  isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white',
                )
              }
            >
              {t(item.labelKey)}
            </NavLink>
          ))}
        </nav>
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button type="button" className="absolute inset-0 bg-black/45" onClick={onClose} aria-label={t('header.close_navigation')} />
          <aside className="relative z-50 h-full w-72 max-w-[85vw] bg-gray-900 text-white">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <img src="/logo.png" alt="DeskSupportMonkey" className="w-9 h-9 rounded" />
                <div>
                  <h1 className="text-lg font-bold tracking-tight leading-tight">DSM</h1>
                  <p className="text-xs text-gray-400">DeskSupportMonkey</p>
                </div>
              </div>
              <button type="button" onClick={onClose} className="rounded-md p-1 text-gray-300 hover:bg-gray-800" aria-label={t('header.close_navigation')} title={t('header.close_navigation')}>
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <nav className="p-2 space-y-0.5">
              {visible.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    cn(
                      'block px-3 py-2 rounded text-sm transition-colors',
                      isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white',
                    )
                  }
                >
                  {t(item.labelKey)}
                </NavLink>
              ))}
            </nav>
          </aside>
        </div>
      )}
    </>
  );
}
