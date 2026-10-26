import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import useCurrentUser from '../hooks/useCurrentUser';

export default function Home() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();

  useEffect(() => {
    if (!loading) {
      router.replace(user ? '/estate-dashboard' : '/login');
    }
  }, [user, loading, router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-slate-100">
      <div className="text-center">
        <p className="text-sm text-slate-400">{loading || !router.isReady ? 'Checking session...' : 'Opening Aegis...'}</p>
        {!loading && router.isReady && (
          <Link href={user ? '/estate-dashboard' : '/login'} className="mt-3 inline-block text-sm text-cyan-300 hover:text-cyan-100">
            Continue
          </Link>
        )}
      </div>
    </main>
  );
}
