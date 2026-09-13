import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function LegacyDashboard3D() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/3d-scene');
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-300">
      <div className="text-center">
        <p className="text-xs uppercase tracking-[0.3em] text-cyan-400">Redirecting</p>
        <p className="mt-3 text-lg text-slate-200">Loading the current 3D estate scene…</p>
      </div>
    </div>
  );
}
