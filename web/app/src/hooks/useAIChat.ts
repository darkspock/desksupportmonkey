import { useState, useCallback } from 'react';
import api from '../lib/api';
import { useI18n } from '../lib/i18n';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function useAIChat() {
  const { t } = useI18n();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    setError(null);
    const userMsg: ChatMessage = { role: 'user', content, timestamp: new Date() };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setIsLoading(true);

    try {
      const apiMessages = updatedMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const { data } = await api.post('/my/ai-support', { messages: apiMessages });
      const aiMsg: ChatMessage = {
        role: 'assistant',
        content: data.data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 429) {
        setError(t('ai_chat.rate_limit'));
      } else if (status === 503) {
        setError(t('ai_chat.unavailable'));
      } else {
        setError(t('ai_chat.error'));
      }
    } finally {
      setIsLoading(false);
    }
  }, [messages, t]);

  const resetChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isLoading, error, sendMessage, resetChat };
}
