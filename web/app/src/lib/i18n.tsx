/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import en from '../locales/en';
import es from '../locales/es';

export type AppLanguage = 'en' | 'es';

type TranslateParams = Record<string, string | number>;

interface TranslateOptions {
  defaultValue?: string;
}

interface I18nContextValue {
  language: AppLanguage;
  setLanguage: (language: AppLanguage) => void;
  t: (key: string, params?: TranslateParams, options?: TranslateOptions) => string;
}

const STORAGE_KEY = 'dsm.language';
const dictionaries: Record<AppLanguage, Record<string, string>> = { en, es };

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

function detectLanguage(): AppLanguage {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'en' || stored === 'es') return stored;

  const browserLang = navigator.language.toLowerCase();
  return browserLang.startsWith('es') ? 'es' : 'en';
}

function interpolate(template: string, params?: TranslateParams): string {
  if (!params) return template;
  return template.replace(/\{\{(\w+)\}\}/g, (_, token: string) => String(params[token] ?? `{{${token}}}`));
}

export function humanizeToken(value: string): string {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<AppLanguage>(detectLanguage);

  const setLanguage = (nextLanguage: AppLanguage) => {
    setLanguageState(nextLanguage);
    localStorage.setItem(STORAGE_KEY, nextLanguage);
  };

  const value = useMemo<I18nContextValue>(
    () => ({
      language,
      setLanguage,
      t: (key: string, params?: TranslateParams, options?: TranslateOptions) => {
        const dictionary = dictionaries[language];
        const fallback = dictionaries.en[key] ?? options?.defaultValue ?? key;
        const text = dictionary[key] ?? fallback;
        return interpolate(text, params);
      },
    }),
    [language],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return ctx;
}
