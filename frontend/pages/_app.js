import '../styles/globals.css'
import { useRouter } from 'next/router';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import Main from '../components/Main';
import ProtectedRoute from '../components/ProtectedRoute';
import { ToastProvider } from '../components/ToastContext';
import ErrorBoundary from '../components/ErrorBoundary';
import { useEffect } from 'react';
import { getAuthToken } from '../utils/auth';

const publicPaths = ['/login', '/signup', '/reset-password'];

function MyApp({ Component, pageProps }) {
  const router = useRouter();
  const isPublicRoute = publicPaths.includes(router.pathname);

  useEffect(() => {
    const handler = (e) => {
      // When backend signals unauthorized, clear token and redirect to login once
      try {
        localStorage.removeItem('aegis_token');
      } catch (err) {}
      if (router.pathname !== '/login') {
        router.replace('/login');
      }
    };

    window.addEventListener('aegis:unauthorized', handler);
    return () => window.removeEventListener('aegis:unauthorized', handler);
  }, [router]);

  if (isPublicRoute) {
    return (
      <ErrorBoundary>
        <Component {...pageProps} />
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <ToastProvider>
        <div className="aegis-app-shell min-h-screen flex bg-[#050816]">
          <Sidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header />
            <Main>
              <ProtectedRoute>
                <Component {...pageProps} />
              </ProtectedRoute>
            </Main>
          </div>
        </div>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default MyApp
