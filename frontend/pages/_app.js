import '../styles/globals.css'
import { useRouter } from 'next/router';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import Main from '../components/Main';
import ProtectedRoute from '../components/ProtectedRoute';
import { ToastProvider } from '../components/ToastContext';
import ErrorBoundary from '../components/ErrorBoundary';

const publicPaths = ['/login', '/signup', '/reset-password'];

function MyApp({ Component, pageProps }) {
  const router = useRouter();
  const isPublicRoute = publicPaths.includes(router.pathname);

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
        <div className="min-h-screen flex bg-[#050816]">
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
