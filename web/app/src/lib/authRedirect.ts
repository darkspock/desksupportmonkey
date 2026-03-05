import { getSafeReturnTo } from './navigation';

type RedirectHandler = (to: string) => void;

let redirectHandler: RedirectHandler | null = null;

export function setAuthRedirectHandler(handler: RedirectHandler | null) {
  redirectHandler = handler;
}

export function redirectToLogin(returnTo?: string | null, loginPath = '/auth/login') {
  const safeReturnTo = getSafeReturnTo(returnTo);
  const next = safeReturnTo
    ? `${loginPath}?returnTo=${encodeURIComponent(safeReturnTo)}`
    : loginPath;

  if (redirectHandler) {
    redirectHandler(next);
    return;
  }

  if (typeof window !== 'undefined') {
    window.location.href = next;
  }
}
