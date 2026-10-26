import { useState, useEffect } from 'react';
import { Shield } from 'lucide-react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import Input from '../components/Input';
import Button from '../components/Button';
import { getCurrentUser, loginAPI } from '../utils/api';
import { clearAuthToken, getAuthToken, setAuthToken, setRefreshToken } from '../utils/auth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const router = useRouter();

  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;

    getCurrentUser(token)
      .then(() => router.replace('/estate-dashboard'))
      .catch(() => {
        clearAuthToken();
      });
  }, [router]);

  useEffect(() => {
    if (router.query.registered === '1') {
      setErrorMsg('Account created. Sign in to continue.');
    }
  }, [router.query.registered]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    
    try {
      const data = await loginAPI(email, password);
      setAuthToken(data.access_token);
      setRefreshToken(data.refresh_token);
      router.replace('/estate-dashboard');
    } catch (error) {
      setErrorMsg(error.message || 'Sign-in failed. Check your credentials and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1120] flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans text-aegis-text relative overflow-hidden">
      <Head>
        <title>Aegis OS | Zero-Trust Authentication</title>
      </Head>

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="rounded-3xl border border-slate-700 bg-[#08101d] p-8 shadow-aet text-center">
          <div className="flex justify-center mb-4 text-aegis-primary">
            <Shield size={48} strokeWidth={1.5} />
          </div>
          <h2 className="text-center text-3xl font-extrabold tracking-tight text-white">
            AEGIS OS
          </h2>
          <p className="mt-2 text-center text-sm text-aegis-muted max-w-md mx-auto">
            Sign in to the sovereign audit control center and manage zones, sensors, and compliance flows.
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="glass-card glow-border py-8 px-6 sm:px-10 sm:rounded-4xl">
          
          {errorMsg && (
            <div role="alert" className="mb-4 bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded text-sm text-center">
              {errorMsg}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleLogin}>
            <Input 
              label="Operator ID (Email)" 
              type="email" 
              id="email" 
              autoComplete="username"
              placeholder="admin@aegis.com" 
              required={true}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <Input 
              label="Passphrase" 
              type="password" 
              id="password" 
              autoComplete="current-password"
              minLength={6}
              placeholder="••••••••••••" 
              required={true}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <Button 
              type="submit" 
              variant="primary" 
              disabled={isLoading}
              className="w-full flex justify-center py-3 text-lg"
            >
              {isLoading ? 'Authenticating...' : 'Initialize Session'}
            </Button>
          </form>
          <div className="mt-6 text-center text-sm text-aegis-muted">
            Access is granted only to verified operators. All sessions are logged immutably.
          </div>
          <div className="mt-4 text-center text-sm text-aegis-muted">
            New operator?{' '}
            <Link href="/signup" className="font-semibold text-aegis-primary hover:text-blue-400 transition-colors">
              Create an account
            </Link>
          </div>
          <div className="mt-3 text-center text-sm">
            <Link href="/reset-password" className="font-semibold text-aegis-primary hover:text-blue-400 transition-colors">Reset password</Link>
          </div>
        </div>
      </div>
    </div>
  );
}