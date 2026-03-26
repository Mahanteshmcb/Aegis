import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

export default function ProtectedRoute({ children }) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('aegis_token');
    
    if (!token) {
      // No token? Send them to login immediately
      router.push('/login');
    } else {
      // In Phase 2, we would validate the token with the backend here
      setIsAuthenticated(true);
    }
  }, [router]);

  // Show nothing while checking or if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#0b1120] flex items-center justify-center">
        <div className="animate-pulse text-aegis-primary font-mono">
          AUTHENTICATING OPERATOR...
        </div>
      </div>
    );
  }

  return children;
}