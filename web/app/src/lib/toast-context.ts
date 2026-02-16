import { createContext } from 'react';

export type ToastVariant = 'success' | 'error' | 'info';

export interface ToastInput {
  title: string;
  description?: string;
  variant?: ToastVariant;
  durationMs?: number;
}

export interface ToastContextValue {
  showToast: (input: ToastInput) => void;
}

export const ToastContext = createContext<ToastContextValue | null>(null);
