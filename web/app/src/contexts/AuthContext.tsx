/* eslint-disable react-hooks/set-state-in-effect, react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import api from '../lib/api';
import { AUTH_UNAUTHORIZED_EVENT } from '../lib/authEvents';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
}

interface AuthContextType extends AuthState {
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isRole: (...roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem('token'),
    loading: true,
  });

  const fetchUser = useCallback(async (token: string) => {
    try {
      const { data } = await api.get('/auth/me');
      setState({ user: data.data, token, loading: false });
    } catch {
      localStorage.removeItem('token');
      setState({ user: null, token: null, loading: false });
    }
  }, []);

  useEffect(() => {
    if (state.token) {
      fetchUser(state.token);
    } else {
      setState((s) => ({ ...s, loading: false }));
    }
  }, [fetchUser, state.token]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleUnauthorized = () => {
      setState({ user: null, token: null, loading: false });
    };

    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => {
      window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);
    };
  }, []);

  const login = async (token: string) => {
    localStorage.setItem('token', token);
    await fetchUser(token);
  };

  const refreshUser = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      await fetchUser(token);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setState({ user: null, token: null, loading: false });
  };

  const isRole = (...roles: string[]) => {
    if (!state.user) return false;
    return roles.includes(state.user.role);
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout, refreshUser, isRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
}
