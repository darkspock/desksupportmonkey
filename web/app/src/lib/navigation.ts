import type { UserRole } from '../types';

export function getDefaultRouteForRole(role?: UserRole | null): string {
  switch (role) {
    case 'super_admin':
      return '/overview';
    case 'admin':
      return '/dashboard';
    case 'procurement_manager':
    case 'technician':
      return '/requests';
    case 'employee':
    default:
      return '/my/equipment';
  }
}

export function getSafeReturnTo(value: string | null | undefined): string | null {
  if (!value) return null;

  const trimmed = value.trim();
  if (!trimmed.startsWith('/')) return null;
  if (trimmed.startsWith('//')) return null;
  if (trimmed.startsWith('/auth/')) return null;

  return trimmed;
}

export function currentPathWithQuery(): string {
  if (typeof window === 'undefined') return '/';
  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
}
