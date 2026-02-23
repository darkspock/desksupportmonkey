import { useEffect, useState, useCallback, type ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '../../lib/cn';
import { useI18n } from '../../lib/i18n';

/* ------------------------------------------------------------------ */
/* Icons – Heroicons-style outline SVGs (24×24, strokeWidth 1.5)      */
/* ------------------------------------------------------------------ */

const icon = (d: string) => (
  <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);

const icons: Record<string, ReactNode> = {
  // My Activity
  '/my/equipment':   icon('M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25A2.25 2.25 0 0 1 5.25 3h13.5A2.25 2.25 0 0 1 21 5.25Z'),
  '/my/requests':    icon('M11.35 3.836c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15a2.25 2.25 0 0 1 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V19.5a2.625 2.625 0 0 0 2.625 2.625h6.75a2.625 2.625 0 0 0 2.625-2.625V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664'),
  '/my/appointments': icon('M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5m-9-6h.008v.008H12v-.008ZM12 15h.008v.008H12V15Zm0 2.25h.008v.008H12v-.008ZM9.75 15h.008v.008H9.75V15Zm0 2.25h.008v.008H9.75v-.008ZM7.5 15h.008v.008H7.5V15Zm0 2.25h.008v.008H7.5v-.008Zm6.75-4.5h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V15Zm0 2.25h.008v.008h-.008v-.008Zm2.25-4.5h.008v.008H16.5v-.008Zm0 2.25h.008v.008H16.5V15Z'),
  '/my/shipments':   icon('M8.25 18.75a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 0 1-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 0 0-3.213-9.193 2.056 2.056 0 0 0-1.58-.86H14.25M2.25 14.25V5.625c0-.621.504-1.125 1.125-1.125h8.25c.621 0 1.125.504 1.125 1.125v8.625m0 0h5.25M14.25 7.5v5.25'),
  '/my/maintenance': icon('M11.42 15.17 17.25 21A2.652 2.652 0 0 0 21 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 1 1-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 0 0 4.486-6.336l-3.276 3.277a3.004 3.004 0 0 1-2.25-2.25l3.276-3.276a4.5 4.5 0 0 0-6.336 4.486c.049.58.025 1.193-.14 1.743'),
  '/my/tasks/appointments': icon('M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5m-9-6h.008v.008H12v-.008ZM12 15h.008v.008H12V15Zm0 2.25h.008v.008H12v-.008ZM9.75 15h.008v.008H9.75V15Zm0 2.25h.008v.008H9.75v-.008ZM7.5 15h.008v.008H7.5V15Zm0 2.25h.008v.008H7.5v-.008Zm6.75-4.5h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V15Zm0 2.25h.008v.008h-.008v-.008Zm2.25-4.5h.008v.008H16.5v-.008Zm0 2.25h.008v.008H16.5V15Z'),

  // Operations
  '/dashboard':       icon('M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25a2.25 2.25 0 0 1-2.25-2.25v-2.25Z'),
  '/requests':        icon('M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 0 1 0 3.75H5.625a1.875 1.875 0 0 1 0-3.75Z'),
  '/calendar':        icon('M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5'),
  '/assets':          icon('M20.25 7.5l-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z'),
  '/vendors':         icon('M13.5 21v-7.5a.75.75 0 0 1 .75-.75h3a.75.75 0 0 1 .75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349M3.75 21V9.349m0 0a3.001 3.001 0 0 0 3.75-.615A2.993 2.993 0 0 0 9.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 0 0 2.25 1.016c.896 0 1.7-.393 2.25-1.015a3.001 3.001 0 0 0 3.75.614m-16.5 0a3.004 3.004 0 0 1-.621-4.72l1.189-1.19A1.5 1.5 0 0 1 5.378 3h13.243a1.5 1.5 0 0 1 1.06.44l1.19 1.189a3 3 0 0 1-.621 4.72'),
  '/purchase-orders': icon('M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z'),
  '/shipments':       icon('M8.25 18.75a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 0 1-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 0 0-3.213-9.193 2.056 2.056 0 0 0-1.58-.86H14.25M2.25 14.25V5.625c0-.621.504-1.125 1.125-1.125h8.25c.621 0 1.125.504 1.125 1.125v8.625m0 0h5.25M14.25 7.5v5.25'),
  '/maintenance':     icon('M11.42 15.17 17.25 21A2.652 2.652 0 0 0 21 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 1 1-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 0 0 4.486-6.336l-3.276 3.277a3.004 3.004 0 0 1-2.25-2.25l3.276-3.276a4.5 4.5 0 0 0-6.336 4.486c.049.58.025 1.193-.14 1.743'),
  '/addresses':       icon('M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z'),

  // Management
  '/users':                          icon('M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z'),
  '/departments':                    icon('M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21'),
  '/reports':                        icon('M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z'),
  '/settings/company':               icon('M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z'),
  '/settings/api-keys':              icon('M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z'),
  '/settings/employee-roles':        icon('M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z'),
  '/settings/equipment-profiles':    icon('M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75'),
  '/settings/assignment-ai':         icon('M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z'),
  '/settings/availability':          icon('M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z'),
  '/settings/request-classification': icon('M9.568 3H5.25A2.25 2.25 0 0 0 3 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 0 0 5.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 0 0 9.568 3Z M6 6h.008v.008H6V6Z'),
  '/settings/procurement':           icon('M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18v-.008Zm-12 0h.008v.008H6v-.008Z'),
  '/maintenance-templates':          icon('M8.25 7.5V6.108c0-1.135.845-2.098 1.976-2.192.373-.03.748-.057 1.123-.08M15.75 18H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08M15.75 18.75v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5A3.375 3.375 0 0 0 6.375 7.5H5.25m11.9-3.664A2.251 2.251 0 0 0 13.5 2.25H15a2.25 2.25 0 0 1 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m8.9-4.414c.376.023.75.05 1.124.08 1.131.094 1.976 1.057 1.976 2.192V16.5A2.25 2.25 0 0 1 18 18.75h-2.25m-7.5-10.5H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V18.75m-7.5-10.5h6.375c.621 0 1.125.504 1.125 1.125v9.375m-8.25-3 1.5 1.5 3-3.75'),
  '/billing':                        icon('M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Z'),

  // Platform
  '/overview':        icon('M10.5 6a7.5 7.5 0 1 0 7.5 7.5h-7.5V6Z M13.5 3.5a7.5 7.5 0 0 1 7 7.5h-7V3.5Z'),
  '/companies':       icon('M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z'),
};

/* ------------------------------------------------------------------ */
/* Data                                                                */
/* ------------------------------------------------------------------ */

interface NavItem {
  type?: undefined;
  to: string;
  labelKey: string;
  roles?: string[];
}

interface NavSeparator {
  type: 'separator';
  roles?: string[];
}

interface NavSubGroup {
  type: 'subgroup';
  labelKey: string;
  roles?: string[];
  items: NavItem[];
}

type NavEntry = NavItem | NavSeparator | NavSubGroup;

interface NavSection {
  labelKey?: string;
  items: NavEntry[];
}

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

const sections: NavSection[] = [
  {
    labelKey: 'nav.section_my_activity',
    items: [
      { to: '/my/equipment', labelKey: 'nav.my_equipment' },
      { to: '/my/requests', labelKey: 'nav.my_requests' },
      { to: '/my/appointments', labelKey: 'nav.my_appointments' },
      { to: '/my/shipments', labelKey: 'nav.my_shipments' },
    ],
  },
  {
    labelKey: 'nav.section_my_tasks',
    items: [
      { to: '/my/tasks/appointments', labelKey: 'nav.my_task_appointments', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/my/maintenance', labelKey: 'nav.my_maintenance', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
    ],
  },
  {
    labelKey: 'nav.section_operations',
    items: [
      { to: '/dashboard', labelKey: 'nav.dashboard', roles: ['admin', 'super_admin'] },
      { to: '/requests', labelKey: 'nav.request_queue', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/calendar', labelKey: 'nav.calendar', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/assets', labelKey: 'nav.asset_inventory', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/vendors', labelKey: 'nav.vendors', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/purchase-orders', labelKey: 'nav.purchase_orders', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/shipments', labelKey: 'nav.shipments', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/maintenance', labelKey: 'nav.maintenance', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/addresses', labelKey: 'nav.addresses', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
    ],
  },
  {
    labelKey: 'nav.section_management',
    items: [
      {
        type: 'subgroup', labelKey: 'nav.subgroup_people', roles: ['admin', 'super_admin'],
        items: [
          { to: '/users', labelKey: 'nav.users', roles: ['admin', 'super_admin'] },
          { to: '/departments', labelKey: 'nav.departments', roles: ['admin', 'super_admin'] },
          { to: '/settings/employee-roles', labelKey: 'nav.employee_roles', roles: ['admin', 'super_admin'] },
        ],
      },
      {
        type: 'subgroup', labelKey: 'nav.subgroup_configuration', roles: ['admin'],
        items: [
          { to: '/settings/company', labelKey: 'nav.company_settings', roles: ['admin'] },
          { to: '/settings/request-classification', labelKey: 'nav.request_classification', roles: ['admin'] },
          { to: '/maintenance-templates', labelKey: 'nav.maintenance_templates', roles: ['admin', 'super_admin'] },
          { to: '/settings/assignment-ai', labelKey: 'nav.assignment_ai', roles: ['admin'] },
          { to: '/settings/availability', labelKey: 'nav.availability_settings', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
        ],
      },
      {
        type: 'subgroup', labelKey: 'nav.subgroup_procurement', roles: ['admin'],
        items: [
          { to: '/settings/equipment-profiles', labelKey: 'nav.equipment_profiles', roles: ['admin', 'super_admin'] },
          { to: '/settings/procurement', labelKey: 'nav.procurement_settings', roles: ['admin'] },
        ],
      },
      {
        type: 'subgroup', labelKey: 'nav.subgroup_advanced', roles: ['admin', 'super_admin'],
        items: [
          { to: '/settings/api-keys', labelKey: 'nav.api_keys', roles: ['admin', 'super_admin'] },
        ],
      },
      { to: '/reports', labelKey: 'nav.reports', roles: ['admin', 'super_admin'] },
      { to: '/billing', labelKey: 'nav.billing', roles: ['admin'] },
    ],
  },
  {
    labelKey: 'nav.section_platform',
    items: [
      { to: '/overview', labelKey: 'nav.overview', roles: ['super_admin'] },
      { to: '/companies', labelKey: 'nav.companies', roles: ['super_admin'] },
    ],
  },
];

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export function Sidebar({ mobileOpen = false, onClose }: SidebarProps) {
  const { user } = useAuth();
  const { t } = useI18n();
  const role = user?.role;
  const companyName = user?.company_name?.trim() || user?.email || 'DeskSupportMonkey';

  const isSeparator = (entry: NavEntry): entry is NavSeparator => entry.type === 'separator';
  const isSubGroup = (entry: NavEntry): entry is NavSubGroup => entry.type === 'subgroup';
  const isNavItem = (entry: NavEntry): entry is NavItem => !entry.type;

  const roleVisible = (entry: { roles?: string[] }) => !entry.roles || (role && entry.roles.includes(role));

  const filterEntries = useCallback((items: NavEntry[]): NavEntry[] => {
    const filtered: NavEntry[] = [];
    for (const item of items) {
      if (!roleVisible(item)) continue;
      if (isSubGroup(item)) {
        const visibleChildren = item.items.filter(roleVisible);
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
      filtered.push(item);
    }
    while (filtered[0] && isSeparator(filtered[0])) filtered.shift();
    while (filtered[filtered.length - 1] && isSeparator(filtered[filtered.length - 1])) filtered.pop();
    return filtered;
  }, [role]); // eslint-disable-line react-hooks/exhaustive-deps

  const baseSections = sections
    .map((section) => ({ ...section, items: filterEntries(section.items) }))
    .filter((section) => section.items.length > 0);

  const superAdminAllowed = new Set(['/overview', '/companies', '/settings/api-keys']);
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
          <img src="/logo.png" alt="DeskSupportMonkey" className="w-5 h-5" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold leading-none text-sidebar-foreground">DS Monkey</span>
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
                  {t(section.labelKey)}
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
                    return (
                      <NavLink
                        key={item.to}
                        to={item.to}
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
