import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';

export default function RegisterPage() {
  const { user } = useAuth();
  const [name, setName] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [emailDomains, setEmailDomains] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const domains = emailDomains
        .split(',')
        .map((d) => d.trim())
        .filter(Boolean);
      if (domains.length === 0) {
        setError('At least one email domain is required');
        setLoading(false);
        return;
      }
      await api.post('/register', {
        name,
        admin_email: adminEmail,
        email_domains: domains,
      });
      setSent(true);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Registration failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-xl shadow-sm border p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Register your company</h1>
          <p className="text-sm text-gray-500 mb-6">Create a new company account</p>

          {sent ? (
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-sm text-gray-600">Company registered! Check your email for the magic link.</p>
              <Link to="/auth/login" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
                Back to login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Company name"
                required
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3"
              />
              <input
                type="email"
                value={adminEmail}
                onChange={(e) => setAdminEmail(e.target.value)}
                placeholder="Admin email"
                required
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3"
              />
              <input
                type="text"
                value={emailDomains}
                onChange={(e) => setEmailDomains(e.target.value)}
                placeholder="Email domains (comma-separated, e.g. company.com)"
                required
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Registering...' : 'Register Company'}
              </button>
              <p className="mt-4 text-center text-sm text-gray-500">
                Already have an account?{' '}
                <Link to="/auth/login" className="text-blue-600 hover:underline">Sign in</Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
