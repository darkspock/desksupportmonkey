import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';

type LoginMode = 'magic-link' | 'password';

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<LoginMode>('magic-link');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/auth/magic-link', { email });
      setSent(true);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to send magic link';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post('/auth/login', { email, password });
      await login(data.data.access_token);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Login failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-xl shadow-sm border p-8">
          <div className="flex items-center justify-center gap-3 mb-1">
            <img src="/logo.png" alt="DeskSupportMonkey" className="w-10 h-10" />
            <h1 className="text-2xl font-bold text-gray-900">DeskSupportMonkey</h1>
          </div>
          <p className="text-sm text-gray-500 mb-6">Sign in with your corporate email</p>

          {/* Tab toggle */}
          <div className="flex mb-5 border rounded-lg overflow-hidden">
            <button
              onClick={() => { setMode('magic-link'); setError(''); }}
              className={`flex-1 py-2 text-sm font-medium ${mode === 'magic-link' ? 'bg-blue-600 text-white' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'}`}
            >
              Magic Link
            </button>
            <button
              onClick={() => { setMode('password'); setError(''); }}
              className={`flex-1 py-2 text-sm font-medium ${mode === 'password' ? 'bg-blue-600 text-white' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'}`}
            >
              Password
            </button>
          </div>

          {mode === 'magic-link' && sent ? (
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-sm text-gray-600">Check your email for the magic link.</p>
              <button onClick={() => setSent(false)} className="mt-4 text-sm text-blue-600 hover:underline">
                Try again
              </button>
            </div>
          ) : mode === 'magic-link' ? (
            <form onSubmit={handleMagicLink}>
              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Send Magic Link'}
              </button>
            </form>
          ) : (
            <form onSubmit={handlePasswordLogin}>
              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3"
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
              <p className="mt-3 text-center text-xs text-gray-400">For admin accounts</p>
            </form>
          )}

          <p className="mt-4 text-center text-sm text-gray-500">
            Don't have an account?{' '}
            <Link to="/auth/register" className="text-blue-600 hover:underline">Register your company</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
