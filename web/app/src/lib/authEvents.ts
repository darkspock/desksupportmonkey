export const AUTH_UNAUTHORIZED_EVENT = 'dsm-auth-unauthorized';

export function emitAuthUnauthorized() {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new Event(AUTH_UNAUTHORIZED_EVENT));
}
