import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { registerAPI } from '../utils/api';
import useCurrentUser from '../hooks/useCurrentUser';

export default function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { user, loading: checkingSession } = useCurrentUser();

  useEffect(() => {
    if (!checkingSession && user) router.replace('/estate-dashboard');
  }, [checkingSession, router, user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (!Number.isInteger(Number(tenantId)) || Number(tenantId) < 1) {
      setError('Enter the tenant ID provided by your administrator.');
      return;
    }
    setLoading(true);
    try {
      const data = await registerAPI(email, password, Number(tenantId));
      if (data) {
        router.push('/login');
      }
    } catch (err) {
      setError(err.message || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-transparent flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
        <h2 className="text-3xl font-extrabold tracking-tight text-white">Create your AEGIS account</h2>
        <p className="mt-2 text-sm text-aegis-muted">Development self-registration creates a read-only account. In production, request access from your tenant administrator.</p>
      </div>
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="glass-card glow-border py-8 px-6 sm:px-10 sm:rounded-4xl">
          <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block mb-1 font-medium" htmlFor="tenant-id">Tenant ID</label>
          <input
            id="tenant-id"
            type="number"
            min="1"
            step="1"
            className="w-full border rounded px-3 py-2"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block mb-1 font-medium" htmlFor="signup-email">Email</label>
          <input
            type="email"
            id="signup-email"
            autoComplete="email"
            className="w-full border rounded px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block mb-1 font-medium" htmlFor="signup-password">Password</label>
          <input
            type="password"
            id="signup-password"
            autoComplete="new-password"
            minLength={6}
            className="w-full border rounded px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block mb-1 font-medium" htmlFor="confirm-password">Confirm Password</label>
          <input
            type="password"
            id="confirm-password"
            autoComplete="new-password"
            minLength={6}
            className="w-full border rounded px-3 py-2"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>
        {error && <div role="alert" className="text-red-300 text-sm">{error}</div>}
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? 'Signing up...' : 'Sign Up'}
        </button>
          </form>
          <div className="mt-6 text-center text-sm text-aegis-muted">
            New accounts start with viewer access. An administrator can change your role.
          </div>
          <div className="mt-4 text-sm text-center">
            <Link href="/login" className="text-aegis-primary hover:text-violet-300 transition-colors">Already have an account? Login</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
