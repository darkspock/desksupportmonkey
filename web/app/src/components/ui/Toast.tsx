import { useContext, useMemo } from 'react';
import { ToastContext } from '../../lib/toast-context';

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within <ToastProvider>');

  return useMemo(() => ({
    ...ctx,
    success: (title: string) => ctx.showToast({ title, variant: 'success' }),
    error: (title: string) => ctx.showToast({ title, variant: 'error' }),
    info: (title: string) => ctx.showToast({ title, variant: 'info' }),
  }), [ctx]);
}
