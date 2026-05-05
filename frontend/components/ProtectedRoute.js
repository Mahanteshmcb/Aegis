import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

export default function ProtectedRoute({ children, requiredRole = null }) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthorized, setIsAuthorized] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('aegis_token');
    
    if (!token) {
      // No token? Send them to login immediately
      router.push('/login');
      return;
    }

    // If a role is required, fetch user data to check
    if (requiredRole) {
      const fetchUser = async () => {
        try {
          const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
          const resp = await fetch(`${API_URL}/api/v1/auth/me`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });

          if (resp.status === 401) {
            router.push('/login');
            return;
          }

          if (!resp.ok) {
            throw new Error('Failed to fetch user');
          }

          const user = await resp.json();
          if (user.role === requiredRole || user.role === 'admin') {
            setIsAuthorized(true);
            setIsAuthenticated(true);
          } else {
            setIsAuthorized(false);
            router.push('/');
          }
        } catch (err) {
          console.error('Auth error:', err);
          router.push('/login');
        }
      };
      fetchUser();
    } else {
      setIsAuthenticated(true);
    }
  }, [router, requiredRole]);

  // Show nothing while checking or if not authenticated
  if (!isAuthenticated || !isAuthorized) {
    return (
      <div className="min-h-screen bg-[#0b1120] flex items-center justify-center">
        <div className="animate-pulse text-aegis-primary font-mono">
          {!isAuthorized ? 'ACCESS DENIED' : 'AUTHENTICATING OPERATOR...'}
        </div>
      </div>
    );
  }

  return children;
}