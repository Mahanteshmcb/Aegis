import { useState, useEffect } from 'react';
import { Shield } from 'lucide-react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Input from '../components/Input';
import Button from '../components/Button';
import { loginAPI } from '../utils/api';
import { getAuthToken, setAuthToken } from '../utils/auth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(''); // NEW: To show bad passwords
  const router = useRouter();

  useEffect(() => {
    if (getAuthToken()) {
      router.replace('/');
    }
  }, [router]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(''); // Clear previous errors
    
    try {
      // 1. Call the FastAPI backend
      const data = await loginAPI(email, password);
      
      // 2. Save the JWT token securely
      // (For Phase 1, localStorage is fine. We can upgrade to httpOnly cookies later)
      setAuthToken(data.access_token);
      console.log('Session Initialized. Token secured.');

      // 3. Redirect to the main dashboard
      router.push('/'); 
      
    } catch (error) {
      // 4. Handle incorrect passwords
      setErrorMsg(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1120] flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans text-aegis-text relative overflow-hidden">
      <Head>
        <title>Aegis OS | Zero-Trust Authentication</title>
      </Head>

      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-aegis-primary/20 blur-[100px] rounded-full pointer-events-none"></div>

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
        <div className="glass-card glow-border py-8 px-6 sm:px-10 sm:rounded-[32px]">
          
          {/* NEW: Error Message Display */}
          {errorMsg && (
            <div className="mb-4 bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded text-sm text-center">
              {errorMsg}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleLogin}>
            <Input 
              label="Operator ID (Email)" 
              type="email" 
              id="email" 
              placeholder="admin@aegis.local" 
              required={true}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <Input 
              label="Passphrase" 
              type="password" 
              id="password" 
              placeholder="••••••••••••" 
              required={true}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 bg-[#0f172a] border-slate-700 rounded text-aegis-primary focus:ring-aegis-primary focus:ring-offset-aegis-dark"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-aegis-muted">
                  Remember device
                </label>
              </div>

              <div className="text-sm">
                <a href="#" className="font-medium text-aegis-primary hover:text-blue-400 transition-colors">
                  Emergency Override?
                </a>
              </div>
            </div>

            <Button 
              type="submit" 
              variant="primary" 
              className="w-full flex justify-center py-3 text-lg"
            >
              {isLoading ? 'Authenticating...' : 'Initialize Session'}
            </Button>
          </form>
          <div className="mt-6 text-center text-sm text-aegis-muted">
            Access is granted only to verified operators. All sessions are logged immutably.
          </div>
        </div>
      </div>
    </div>
  );
}