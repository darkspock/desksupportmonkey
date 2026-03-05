/* eslint-disable react-hooks/set-state-in-effect, react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import api from '../lib/api';
import type { Reseller } from '../types';

const RESELLER_TOKEN_KEY = 'reseller_token';

interface ResellerAuthState {
  reseller: Reseller | null;
  token: string | null;
  loading: boolean;
}

interface ResellerAuthContextType extends ResellerAuthState {
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshReseller: () => Promise<void>;
}

const ResellerAuthContext = createContext<ResellerAuthContextType | null>(null);

export function ResellerAuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<ResellerAuthState>({
    reseller: null,
    token: localStorage.getItem(RESELLER_TOKEN_KEY),
    loading: true,
  });

  const fetchReseller = useCallback(async (token: string) => {
    try {
      const { data } = await api.get('/reseller/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setState({ reseller: data.data, token, loading: false });
    } catch {
      localStorage.removeItem(RESELLER_TOKEN_KEY);
      setState({ reseller: null, token: null, loading: false });
    }
  }, []);

  useEffect(() => {
    if (state.token) {
      fetchReseller(state.token);
    } else {
      setState((s) => ({ ...s, loading: false }));
    }
  }, [fetchReseller, state.token]);

  const login = async (token: string) => {
    localStorage.setItem(RESELLER_TOKEN_KEY, token);
    await fetchReseller(token);
  };

  const refreshReseller = async () => {
    const token = localStorage.getItem(RESELLER_TOKEN_KEY);
    if (token) {
      await fetchReseller(token);
    }
  };

  const logout = () => {
    localStorage.removeItem(RESELLER_TOKEN_KEY);
    setState({ reseller: null, token: null, loading: false });
  };

  return (
    <ResellerAuthContext.Provider value={{ ...state, login, logout, refreshReseller }}>
      {children}
    </ResellerAuthContext.Provider>
  );
}

export function useResellerAuth() {
  const ctx = useContext(ResellerAuthContext);
  if (!ctx) throw new Error('useResellerAuth must be inside ResellerAuthProvider');
  return ctx;
}
