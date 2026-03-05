import axios from 'axios';
import { currentPathWithQuery } from './navigation';
import { emitAuthUnauthorized } from './authEvents';
import { redirectToLogin } from './authRedirect';

function normalizeErrorDetail(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') return null;

  const asRecord = payload as Record<string, unknown>;
  const directDetail = asRecord.detail;
  if (typeof directDetail === 'string' && directDetail.trim()) {
    return directDetail;
  }

  const directMessage = asRecord.message;
  if (typeof directMessage === 'string' && directMessage.trim()) {
    return directMessage;
  }

  const nestedError = asRecord.error;
  if (nestedError && typeof nestedError === 'object') {
    const nestedMessage = (nestedError as Record<string, unknown>).message;
    if (typeof nestedMessage === 'string' && nestedMessage.trim()) {
      return nestedMessage;
    }
  }

  return null;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (config.headers.Authorization) {
    return config;
  }
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const payload = error?.response?.data;
    const normalizedDetail = normalizeErrorDetail(payload);
    if (normalizedDetail && payload && typeof payload === 'object') {
      error.response.data = {
        ...(payload as Record<string, unknown>),
        detail: normalizedDetail,
      };
    }

    if (error.response?.status === 401) {
      const current = currentPathWithQuery();
      const isAuthPath = current.startsWith('/auth/');

      localStorage.removeItem('token');
      emitAuthUnauthorized();

      if (!isAuthPath) {
        redirectToLogin(current);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
