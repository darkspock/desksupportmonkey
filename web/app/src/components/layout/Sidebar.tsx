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

interface NavSection {
  labelKey?: string;
  items: NavItem[];
}

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

const sections: NavSection[] = [
  {
    items: [
      { to: '/my/equipment', labelKey: 'nav.my_equipment' },
      { to: '/my/requests', labelKey: 'nav.my_requests' },
      { to: '/my/appointments', labelKey: 'nav.my_appointments' },
      { to: '/my/shipments', labelKey: 'nav.my_shipments' },
      { to: '/my/maintenance', labelKey: 'nav.my_maintenance', roles: ['technician', 'admin', 'super_admin'] },
    ],
  },
  {
    labelKey: 'nav.section_operations',
    items: [
      { to: '/dashboard', labelKey: 'nav.dashboard', roles: ['admin', 'super_admin'] },
      { to: '/requests', labelKey: 'nav.request_queue', roles: ['technician', 'admin', 'super_admin'] },
      { to: '/calendar', labelKey: 'nav.calendar', roles: ['technician', 'admin', 'super_admin'] },
      { to: '/assets', labelKey: 'nav.asset_inventory', roles: ['technician', 'admin', 'super_admin'] },
      { to: '/vendors', labelKey: 'nav.vendors', roles: ['technician', 'admin', 'super_admin'] },
      { to: '/purchase-orders', labelKey: 'nav.purchase_orders', roles: ['technician', 'admin', 'super_admin'] },
      { to: '/shipments', labelKey: 'nav.shipments', roles: ['technician', 'admin', 'super_admin'] },
      { to: '/maintenance', labelKey: 'nav.maintenance', roles: ['technician', 'admin', 'super_admin'] },
      { to: '/addresses', labelKey: 'nav.addresses', roles: ['technician', 'admin', 'super_admin'] },
    ],
  },
  {
    labelKey: 'nav.section_management',
    items: [
      { to: '/users', labelKey: 'nav.users', roles: ['admin', 'super_admin'] },
      { to: '/departments', labelKey: 'nav.departments', roles: ['admin', 'super_admin'] },
      { to: '/reports', labelKey: 'nav.reports', roles: ['admin', 'super_admin'] },
      { to: '/settings/company', labelKey: 'nav.company_settings', roles: ['admin'] },
      { to: '/settings/api-keys', labelKey: 'nav.api_keys', roles: ['admin', 'super_admin'] },
      { to: '/settings/equipment-profiles', labelKey: 'nav.equipment_profiles', roles: ['admin', 'super_admin'] },
      { to: '/settings/assignment-ai', labelKey: 'nav.assignment_ai', roles: ['admin'] },
      { to: '/settings/availability', labelKey: 'nav.availability_settings', roles: ['technician', 'admin', 'super_admin'] },
      { to: '/settings/request-classification', labelKey: 'nav.request_classification', roles: ['admin'] },
      { to: '/settings/procurement', labelKey: 'nav.procurement_settings', roles: ['admin'] },
      { to: '/maintenance-templates', labelKey: 'nav.maintenance_templates', roles: ['admin', 'super_admin'] },
    ],
  },
  {
    labelKey: 'nav.section_platform',
    items: [
      { to: '/companies', labelKey: 'nav.companies', roles: ['super_admin'] },
    ],
  },
];

export function Sidebar({ mobileOpen = false, onClose }: SidebarProps) {
  const { user } = useAuth();
  const { t } = useI18n();
  const role = user?.role;
  const companyName = user?.company_name?.trim() || user?.email || 'DeskSupportMonkey';

  const baseSections = sections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => !item.roles || (role && item.roles.includes(role))),
    }))
    .filter((section) => section.items.length > 0);

  const visibleSections = role === 'super_admin'
    ? baseSections
      .map((section) => ({
        ...section,
        items: section.items.filter((item) => item.to === '/companies' || item.to === '/settings/api-keys'),
      }))
      .filter((section) => section.items.length > 0)
    : baseSections;

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

  const navContent = (closeFn?: () => void) => (
    <>
      <div className="p-4 border-b border-sidebar-border flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar-primary">
          <img src="/logo.png" alt="DeskSupportMonkey" className="w-5 h-5" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold leading-none text-sidebar-foreground">DS Monkey</span>
          <span className="max-w-[140px] truncate text-[10px] text-sidebar-foreground/60 leading-none mt-0.5" title={companyName}>
            {companyName}
          </span>
        </div>
      </div>
      <nav className="flex-1 p-2 space-y-4 overflow-y-auto">
        {visibleSections.map((section, i) => (
          <div key={i}>
            {section.labelKey && (
              <p className="px-3 mb-1 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/40">
                {t(section.labelKey)}
              </p>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={closeFn}
                  className={({ isActive }) =>
                    cn(
                      'block px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                        : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                    )
                  }
                >
                  {t(item.labelKey)}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </>
  );

  return (
    <>
      <aside className="hidden w-56 shrink-0 bg-sidebar text-sidebar-foreground min-h-screen md:flex md:flex-col">
        {navContent()}
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button type="button" className="absolute inset-0 bg-black/45" onClick={onClose} aria-label={t('header.close_navigation')} />
          <aside className="relative z-50 h-full w-72 max-w-[85vw] bg-sidebar text-sidebar-foreground flex flex-col">
            {navContent(onClose)}
          </aside>
        </div>
      )}
    </>
  );
}
