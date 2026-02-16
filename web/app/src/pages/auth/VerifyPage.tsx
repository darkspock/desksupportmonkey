import { useEffect, useState } from 'react';
import { useSearchParams, Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';

export default function VerifyPage() {
  const [params] = useSearchParams();
  const { login, user } = useAuth();
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    const token = params.get('token');
    if (!token) {
      setError('Missing token');
      return;
    }
    api.post('/auth/verify', { token })
      .then(async (res) => {
        await login(res.data.data.access_token);
        setDone(true);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Verification failed');
      });
  }, []);

  if (done || user) return <Navigate to="/" replace />;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-xl shadow-sm border p-8 w-full max-w-sm text-center">
        {error ? (
          <>
            <p className="text-red-600 mb-4">{error}</p>
            <a href="/login" className="text-sm text-blue-600 hover:underline">Back to login</a>
          </>
        ) : (
          <>
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mx-auto mb-4" />
            <p className="text-sm text-gray-500">Verifying...</p>
          </>
        )}
      </div>
    </div>
  );
}
