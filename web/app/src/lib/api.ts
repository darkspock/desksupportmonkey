import axios from 'axios';
import { currentPathWithQuery } from './navigation';
import { emitAuthUnauthorized } from './authEvents';
import { redirectToLogin } from './authRedirect';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      emitAuthUnauthorized();

      const current = currentPathWithQuery();
      const isAuthPath = current.startsWith('/auth/');
      if (!isAuthPath) {
        redirectToLogin(current);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
