import { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './components/ui/ToastProvider';
import { I18nProvider } from './lib/i18n';
import { router } from './router';
import { setAuthRedirectHandler } from './lib/authRedirect';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30000 },
  },
});

export default function App() {
  useEffect(() => {
    setAuthRedirectHandler((to) => {
      void router.navigate(to, { replace: true });
    });

    return () => {
      setAuthRedirectHandler(null);
    };
  }, []);

  return (
    <I18nProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ToastProvider>
            <RouterProvider router={router} />
          </ToastProvider>
        </AuthProvider>
      </QueryClientProvider>
    </I18nProvider>
  );
}
