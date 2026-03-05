import { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { HelpCircle, X, Bot } from 'lucide-react';
import { useI18n } from '../../lib/i18n';
import { useAuth } from '../../contexts/AuthContext';
import { getHelpKeyForPath } from '../../config/helpContent';

export function HelpPanel() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const { t } = useI18n();
  const { isRole } = useAuth();

  const helpKey = getHelpKeyForPath(location.pathname);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, close]);

  return (
    <>
      {/* Floating help button */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-[80] flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        aria-label={t('help.title')}
      >
        <HelpCircle className="h-6 w-6" />
      </button>

      {/* Slide-in panel */}
      {open && (
        <div className="fixed inset-0 z-[85] flex justify-end">
          {/* Backdrop */}
          <button
            type="button"
            className="absolute inset-0 bg-black/30"
            onClick={close}
            aria-label={t('common.close')}
          />

          {/* Panel */}
          <div className="relative z-10 flex h-full w-full max-w-md flex-col border-l border-border bg-card shadow-xl animate-in slide-in-from-right duration-200">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border p-4">
              <h2 className="text-lg font-semibold text-foreground">
                {t('help.title')}
              </h2>
              <button
                type="button"
                onClick={close}
                className="text-muted-foreground hover:text-foreground text-xl leading-none"
                aria-label={t('common.close')}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
              <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-line">
                {t(helpKey)}
              </p>
            </div>

            {/* Contact footer */}
            <div className="border-t border-border p-4 space-y-3">
              {isRole('admin', 'technician') && (
                <div>
                  <button
                    type="button"
                    onClick={() => {
                      close();
                      window.dispatchEvent(new CustomEvent('open-ai-chat'));
                    }}
                    className="inline-flex items-center gap-1.5 text-sm font-medium text-violet-600 hover:text-violet-700 hover:underline"
                  >
                    <Bot className="h-4 w-4" />
                    {t('ai_chat.title')}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
