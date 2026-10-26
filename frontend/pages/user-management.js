import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function UserManagementRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/admin/users');
  }, [router]);

  return (
    <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-6 text-center text-slate-300">
      <p>Opening user administration... <Link href="/admin/users" className="text-cyan-300">Continue</Link></p>
    </main>
  );
}