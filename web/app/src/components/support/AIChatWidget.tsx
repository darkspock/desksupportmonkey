import { useState, useRef, useEffect } from 'react';
import { Bot, X, Send, Ticket, Loader2 } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useI18n } from '../../lib/i18n';
import { useAIChat } from '../../hooks/useAIChat';
import { AIChatMessage } from './AIChatMessage';

export function AIChatWidget() {
  const { isRole } = useAuth();
  const { t } = useI18n();
  const { messages, isLoading, error, sendMessage } = useAIChat();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Only visible for admin/technician
  if (!isRole('admin', 'technician')) return null;

  const handleSend = () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput('');
    sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Focus input when panel opens
  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  // Listen for custom event from HelpPanel
  useEffect(() => {
    const handler = () => setOpen(true);
    window.addEventListener('open-ai-chat', handler);
    return () => window.removeEventListener('open-ai-chat', handler);
  }, []);

  return (
    <>
      {/* Slide-in panel — opened via HelpPanel's "AI Chat" button */}
      {open && (
        <div className="fixed inset-0 z-[85] flex justify-end">
          {/* Backdrop */}
          <button
            type="button"
            className="absolute inset-0 bg-black/30"
            onClick={() => setOpen(false)}
            aria-label={t('common.close')}
          />

          {/* Panel */}
          <div className="relative z-10 flex h-full w-full max-w-md flex-col border-l border-border bg-card shadow-xl animate-in slide-in-from-right duration-200">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border p-4">
              <div className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-violet-600" />
                <h2 className="text-lg font-semibold text-foreground">
                  {t('ai_chat.title')}
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="text-muted-foreground hover:text-foreground"
                aria-label={t('common.close')}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
              {messages.length === 0 && !isLoading && (
                <div className="flex flex-col items-center justify-center h-full text-center px-4">
                  <Bot className="h-12 w-12 text-violet-600/40 mb-3" />
                  <p className="text-sm text-muted-foreground">
                    {t('ai_chat.welcome')}
                  </p>
                </div>
              )}

              {messages.map((msg, i) => (
                <AIChatMessage key={i} message={msg} />
              ))}

              {isLoading && (
                <div className="flex justify-start mb-3">
                  <div className="bg-muted rounded-xl rounded-bl-sm px-3.5 py-2.5">
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  </div>
                </div>
              )}

              {error && (
                <div className="mb-3 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Footer */}
            <div className="border-t border-border p-4 space-y-3">
              {/* Input */}
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t('ai_chat.placeholder')}
                  maxLength={4000}
                  disabled={isLoading}
                  className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                />
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className="inline-flex items-center justify-center rounded-md h-9 w-9 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                  aria-label={t('ai_chat.send')}
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>

              {/* Escalate button */}
              <button
                type="button"
                onClick={() => {
                  const summary = messages.map(m => `${m.role}: ${m.content}`).join('\n');
                  window.location.href = `/support/tickets/new?ai_summary=${encodeURIComponent(summary)}`;
                }}
                className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                <Ticket className="h-3.5 w-3.5" />
                {t('ai_chat.escalate')}
              </button>

              {/* Disclaimer */}
              <p className="text-[10px] text-muted-foreground leading-tight">
                {t('ai_chat.disclaimer')}
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
