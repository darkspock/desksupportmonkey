import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, Navigate, useSearchParams } from 'react-router-dom';
import { AuthShell } from '../../components/auth/AuthShell';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';
import { getDefaultRouteForRole, getSafeReturnTo } from '../../lib/navigation';
import { useI18n } from '../../lib/i18n';

export default function VerifyPage() {
  const { t } = useI18n();
  const [params] = useSearchParams();
  const token = params.get('token');
  const { login, user } = useAuth();
  const [error, setError] = useState('');
  const [redirect, setRedirect] = useState<string | null>(null);
  const verifyCalledRef = useRef(false);

  const returnTo = useMemo(() => getSafeReturnTo(params.get('returnTo')), [params]);

  useEffect(() => {
    if (!token || verifyCalledRef.current) return;
    verifyCalledRef.current = true;

    api.post('/auth/verify', { token })
      .then(async (res) => {
        const { access_token, password_set } = res.data.data;
        await login(access_token);

        if (password_set === false) {
          setRedirect('/auth/set-password');
        } else {
          setRedirect(returnTo ?? '/');
        }
      })
      .catch((err) => {
        setError(err.response?.data?.detail || t('auth.verify.error_failed'));
      });
  }, [login, returnTo, t, token]);

  if (redirect) return <Navigate to={redirect} replace />;
  if (user && !redirect) return <Navigate to={returnTo ?? getDefaultRouteForRole(user.role)} replace />;

  return (
    <AuthShell title={t('auth.verify.title')} subtitle={t('auth.verify.subtitle')} showBackToLogin={false}>
      {error || !token ? (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-center">
          <p className="text-sm text-destructive">{error || t('auth.verify.missing_token')}</p>
          <Link to="/auth/login" className="mt-3 inline-block text-sm font-medium text-primary hover:underline">
            {t('auth.back_to_login')}
          </Link>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-border bg-secondary py-8">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">{t('auth.verify.verifying')}</p>
        </div>
      )}
    </AuthShell>
  );
}
