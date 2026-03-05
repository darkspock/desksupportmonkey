import { useEffect, useState, useCallback, useMemo, type ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Monitor, ClipboardList, CalendarDays, Truck, TriangleAlert, Wrench,
  ClipboardCheck, CalendarCheck, LayoutDashboard, Inbox, Calendar, Package,
  Store, Share2, ShoppingCart, MapPin, BookOpen, Tag, Clock, ChartColumn,
  FileSearch, ShieldCheck, ShieldAlert, BadgeCheck, Users, Building2, Building,
  Key, UserCog, SlidersHorizontal, Sparkles, Banknote, ListChecks,
  ArrowLeftRight, CreditCard, Eye, ChartPie, ListOrdered,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '../../lib/cn';
import { useI18n } from '../../lib/i18n';
import { brand } from '../../config/brand';
import api from '../../lib/api';
import { sections, type NavEntry, type NavItem, type NavSeparator, type NavSubGroup } from '../../config/navSections';

/* ------------------------------------------------------------------ */
/* Icons (lucide-react)                                                */
/* ------------------------------------------------------------------ */

const cls = 'h-4 w-4 shrink-0';

const icons: Record<string, ReactNode> = {
  // My Activity
  '/my/equipment':          <Monitor className={cls} />,
  '/my/requests':           <ClipboardList className={cls} />,
  '/my/appointments':       <CalendarDays className={cls} />,
  '/my/shipments':          <Truck className={cls} />,
  '/my/incidents':          <TriangleAlert className={cls} />,
  '/my/maintenance':        <Wrench className={cls} />,
  '/my/tasks/requests':     <ClipboardCheck className={cls} />,
  '/my/tasks/appointments': <CalendarCheck className={cls} />,

  // Operations
  '/dashboard':             <LayoutDashboard className={cls} />,
  '/requests':              <Inbox className={cls} />,
  '/calendar':              <Calendar className={cls} />,
  '/assets':                <Package className={cls} />,
  '/vendors':               <Store className={cls} />,
  '/vendors/supply-chain':  <Share2 className={cls} />,
  '/cmdb/dashboard':        <Share2 className={cls} />,
  '/purchase-orders':       <ShoppingCart className={cls} />,
  '/shipments':             <Truck className={cls} />,
  '/maintenance':           <Wrench className={cls} />,
  '/addresses':             <MapPin className={cls} />,

  // Knowledge Base
  '/knowledge-base':        <BookOpen className={cls} />,
  '/kb':                    <BookOpen className={cls} />,
  '/kb/categories':         <Tag className={cls} />,

  // SLA
  '/sla/policies':          <Clock className={cls} />,
  '/sla/dashboard':         <ChartColumn className={cls} />,

  // Security
  '/audit':                       <FileSearch className={cls} />,
  '/incidents':                   <TriangleAlert className={cls} />,
  '/incidents/dashboard':         <ChartColumn className={cls} />,
  '/risks':                       <ShieldCheck className={cls} />,
  '/risks/dashboard':             <LayoutDashboard className={cls} />,
  '/vulnerabilities':             <ShieldAlert className={cls} />,
  '/vulnerabilities/dashboard':   <ChartColumn className={cls} />,
  '/compliance/dashboard':        <BadgeCheck className={cls} />,

  // Management
  '/users':                          <Users className={cls} />,
  '/departments':                    <Building2 className={cls} />,
  '/reports':                        <ChartColumn className={cls} />,
  '/settings/company':               <Building className={cls} />,
  '/settings/api-keys':              <Key className={cls} />,
  '/settings/employee-roles':        <UserCog className={cls} />,
  '/settings/equipment-profiles':    <SlidersHorizontal className={cls} />,
  '/settings/assignment-ai':         <Sparkles className={cls} />,
  '/settings/availability':          <Clock className={cls} />,
  '/settings/request-classification': <Tag className={cls} />,
  '/settings/procurement':           <Banknote className={cls} />,
  '/maintenance-templates':          <ListChecks className={cls} />,
  '/changes':                        <ArrowLeftRight className={cls} />,
  '/changes/dashboard':              <ChartColumn className={cls} />,
  '/billing':                        <CreditCard className={cls} />,
  '/settings/locations':             <MapPin className={cls} />,
  '/settings/compliance':            <BadgeCheck className={cls} />,
  '/settings/gdpr':                  <ShieldCheck className={cls} />,
  '/settings/custom-fields':         <SlidersHorizontal className={cls} />,
  '/settings/asset-types':           <Tag className={cls} />,
  '/settings/workflow-templates':    <ListOrdered className={cls} />,
  '/settings/nav-visibility':        <Eye className={cls} />,
  '/super-admin/audit':              <FileSearch className={cls} />,

  // Platform
  '/overview':              <ChartPie className={cls} />,
  '/companies':             <Building className={cls} />,
  '/resellers':             <Users className={cls} />,
};

/* ------------------------------------------------------------------ */
/* Data (imported from config/navSections.ts)                          */
/* ------------------------------------------------------------------ */

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export function Sidebar({ mobileOpen = false, onClose }: SidebarProps) {
  const { user } = useAuth();
  const { t } = useI18n();
  const role = user?.role;
  const companyName = user?.company_name?.trim() || user?.email || brand.name;
  const isTech = role === 'technician' || role === 'admin' || role === 'super_admin';

  const { data: myTaskCounts } = useQuery({
    queryKey: ['my-task-counts'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/my-tasks/counts');
      return data.data as { requests: number; requests_urgent: number; appointments: number; maintenance: number; total: number; has_urgent: boolean };
    },
    enabled: isTech,
    refetchInterval: 60_000,
  });

  const { data: queueCounts } = useQuery({
    queryKey: ['queue-counts'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/requests/queue-counts');
      return data.data as { urgent: number; total_open: number };
    },
    enabled: isTech,
    refetchInterval: 30_000,
  });

  const navBadgeCounts: Record<string, number> = {
    ...(myTaskCounts ? {
      '/my/tasks/requests': myTaskCounts.requests,
      '/my/tasks/appointments': myTaskCounts.appointments,
      '/my/maintenance': myTaskCounts.maintenance,
    } : {}),
    ...(queueCounts ? {
      '/requests': queueCounts.total_open,
    } : {}),
  };

  // Hidden nav items from company config (skip for admin/super_admin)
  const hiddenPaths = useMemo(() => {
    if (!role || role === 'super_admin') return new Set<string>();
    const paths = user?.hidden_nav_items?.[role];
    return new Set(paths ?? []);
  }, [role, user?.hidden_nav_items]);

  const isSeparator = (entry: NavEntry): entry is NavSeparator => entry.type === 'separator';
  const isSubGroup = (entry: NavEntry): entry is NavSubGroup => entry.type === 'subgroup';
  const isNavItem = (entry: NavEntry): entry is NavItem => !entry.type;

  const roleVisible = (entry: { roles?: string[] }) => !entry.roles || (role && entry.roles.includes(role));
  const notHidden = (entry: NavItem) => !hiddenPaths.has(entry.to);

  const filterEntries = useCallback((items: NavEntry[]): NavEntry[] => {
    const filtered: NavEntry[] = [];
    for (const item of items) {
      if (!roleVisible(item)) continue;
      if (isSubGroup(item)) {
        const visibleChildren = item.items.filter((c) => roleVisible(c) && notHidden(c));
        if (visibleChildren.length > 0) {
          filtered.push({ ...item, items: visibleChildren });
        }
        continue;
      }
      if (isSeparator(item)) {
        if (filtered.length === 0 || isSeparator(filtered[filtered.length - 1])) continue;
        filtered.push(item);
        continue;
      }
      if (!notHidden(item)) continue;
      filtered.push(item);
    }
    while (filtered[0] && isSeparator(filtered[0])) filtered.shift();
    while (filtered[filtered.length - 1] && isSeparator(filtered[filtered.length - 1])) filtered.pop();
    return filtered;
  }, [role, hiddenPaths]); // eslint-disable-line react-hooks/exhaustive-deps

  const baseSections = sections
    .map((section) => ({ ...section, items: filterEntries(section.items) }))
    .filter((section) => section.items.length > 0);

  const superAdminAllowed = new Set(['/overview', '/companies', '/resellers', '/settings/api-keys', '/super-admin/audit']);
  const visibleSections = role === 'super_admin'
    ? baseSections
      .map((section) => ({
        ...section,
        items: filterEntries(
          section.items.filter((item) => isNavItem(item) && superAdminAllowed.has(item.to)),
        ),
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

  const location = useLocation();

  const hasActivePath = (items: NavEntry[]): boolean =>
    items.some((item) => {
      if (isSubGroup(item)) return hasActivePath(item.items);
      if (isNavItem(item)) return location.pathname.startsWith(item.to);
      return false;
    });

  const getInitialCollapsed = useCallback(() => {
    const result: Record<number, boolean> = {};
    visibleSections.forEach((section, i) => {
      if (!section.labelKey) return;
      result[i] = !hasActivePath(section.items);
    });
    return result;
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const getInitialSubGroupCollapsed = useCallback(() => {
    const result: Record<string, boolean> = {};
    visibleSections.forEach((section) => {
      section.items.forEach((item) => {
        if (isSubGroup(item)) {
          result[item.labelKey] = !hasActivePath(item.items);
        }
      });
    });
    return result;
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const [collapsed, setCollapsed] = useState<Record<number, boolean>>(getInitialCollapsed);
  const [subGroupCollapsed, setSubGroupCollapsed] = useState<Record<string, boolean>>(getInitialSubGroupCollapsed);

  const toggleSection = (index: number) => {
    setCollapsed((prev) => {
      const next: Record<number, boolean> = {};
      visibleSections.forEach((section, i) => {
        if (!section.labelKey) return;
        next[i] = i === index ? !prev[i] : true;
      });
      return next;
    });
  };

  const toggleSubGroup = (key: string) => {
    setSubGroupCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const navContent = (closeFn?: () => void) => (
    <>
      <div className="p-4 border-b border-sidebar-border flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar-primary">
          <img src={brand.logoPath} alt={brand.name} className="w-5 h-5" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold leading-none text-sidebar-foreground">{brand.shortName}</span>
          <span className="max-w-[140px] truncate text-[10px] text-sidebar-foreground/60 leading-none mt-0.5" title={companyName}>
            {companyName}
          </span>
        </div>
      </div>
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {visibleSections.map((section, i) => {
          const isCollapsible = Boolean(section.labelKey);
          const isOpen = !isCollapsible || !collapsed[i];

          return (
            <div key={i}>
              {section.labelKey && (
                <button
                  type="button"
                  onClick={() => toggleSection(i)}
                  className="flex w-full items-center justify-between px-3 py-2 mt-2 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/40 hover:text-sidebar-foreground/60 transition-colors"
                >
                  <span className="flex items-center gap-1.5">
                    {t(section.labelKey)}
                    {section.labelKey === 'nav.section_my_tasks' && myTaskCounts && myTaskCounts.total > 0 && (
                      <span className={`rounded-full text-primary-foreground text-[9px] font-bold min-w-[14px] h-3.5 px-1 flex items-center justify-center normal-case tracking-normal ${myTaskCounts.has_urgent ? 'bg-destructive' : 'bg-primary'}`}>
                        {myTaskCounts.total > 99 ? '99+' : myTaskCounts.total}
                      </span>
                    )}
                    {section.labelKey === 'nav.section_operations' && queueCounts && queueCounts.total_open > 0 && (
                      <span className={`rounded-full text-primary-foreground text-[9px] font-bold min-w-[14px] h-3.5 px-1 flex items-center justify-center normal-case tracking-normal ${queueCounts.urgent > 0 ? 'bg-destructive' : 'bg-primary'}`}>
                        {queueCounts.total_open > 99 ? '99+' : queueCounts.total_open}
                      </span>
                    )}
                  </span>
                  <svg
                    viewBox="0 0 24 24"
                    className={cn('h-3.5 w-3.5 transition-transform duration-200', isOpen ? 'rotate-0' : '-rotate-90')}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                  </svg>
                </button>
              )}
              {isOpen && (
                <div className="space-y-0.5">
                  {section.items.map((item, itemIndex) => {
                    if (isSeparator(item)) {
                      return (
                        <div key={`${section.labelKey ?? 'section'}-sep-${itemIndex}`} className="my-1 px-3">
                          <div className="h-px bg-sidebar-border/70" />
                        </div>
                      );
                    }
                    if (isSubGroup(item)) {
                      const sgOpen = !subGroupCollapsed[item.labelKey];
                      return (
                        <div key={item.labelKey}>
                          <button
                            type="button"
                            onClick={() => toggleSubGroup(item.labelKey)}
                            className="flex w-full items-center gap-2.5 px-3 py-2 text-sm font-medium text-sidebar-foreground/50 hover:text-sidebar-foreground/70 transition-colors"
                          >
                            <svg
                              viewBox="0 0 24 24"
                              className={cn('h-3.5 w-3.5 shrink-0 transition-transform duration-200', sgOpen ? 'rotate-0' : '-rotate-90')}
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                            </svg>
                            {t(item.labelKey)}
                          </button>
                          {sgOpen && (
                            <div className="space-y-0.5 ml-2">
                              {item.items.map((child) => (
                                <NavLink
                                  key={child.to}
                                  to={child.to}
                                  end
                                  onClick={closeFn}
                                  className={({ isActive }) =>
                                    cn(
                                      'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                                      isActive
                                        ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                                        : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                                    )
                                  }
                                >
                                  {icons[child.to]}
                                  {t(child.labelKey)}
                                </NavLink>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    }
                    const badgeCount = navBadgeCounts[item.to] ?? 0;
                    return (
                      <NavLink
                        key={item.to}
                        to={item.to}
                        end
                        onClick={closeFn}
                        className={({ isActive }) =>
                          cn(
                            'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                            isActive
                              ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                              : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                          )
                        }
                      >
                        {icons[item.to]}
                        {t(item.labelKey)}
                        {badgeCount > 0 && (
                          <span className={`ml-auto rounded-full text-primary-foreground text-[9px] font-bold min-w-[14px] h-3.5 px-1 flex items-center justify-center ${item.to === '/requests' ? (queueCounts?.urgent ? 'bg-destructive' : 'bg-primary') : (myTaskCounts?.has_urgent ? 'bg-destructive' : 'bg-primary')}`}>
                            {badgeCount > 99 ? '99+' : badgeCount}
                          </span>
                        )}
                      </NavLink>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
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
