import '../styles/globals.css'
import { useRouter } from 'next/router';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import Main from '../components/Main';
import ProtectedRoute from '../components/ProtectedRoute';

const publicPaths = ['/login', '/signup', '/reset-password'];

function MyApp({ Component, pageProps }) {
  const router = useRouter();
  const isPublicRoute = publicPaths.includes(router.pathname);

  if (isPublicRoute) {
    return <Component {...pageProps} />;
  }

  return (
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
  );
}

export default MyApp
