import { useRouter } from 'next/router';
import useCurrentUser from '../hooks/useCurrentUser';

/**
 * RoleBasedRoute: Wrapper for pages that require a specific role.
 * Usage: <RoleBasedRoute requiredRole="admin"><AdminPage /></RoleBasedRoute>
 */
export default function RoleBasedRoute({ children, requiredRole = 'admin' }) {
  const router = useRouter();
  const { user, loading } = useCurrentUser();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b1120] flex items-center justify-center">
        <p className="text-aegis-muted animate-pulse">Verifying access...</p>
      </div>
    );
  }

  // Check if user has required role (admin can access all)
  const hasAccess = user?.role === requiredRole || user?.role === 'admin';

  if (!hasAccess) {
    return (
      <div className="min-h-screen bg-[#0b1120] flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-red-400 mb-4">ACCESS DENIED</h1>
          <p className="text-aegis-muted mb-6">You do not have permission to access this page.</p>
          <p className="text-sm text-aegis-muted mb-8">Required role: <span className="font-bold text-aegis-primary">{requiredRole.toUpperCase()}</span></p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-2 bg-aegis-primary text-white rounded-lg hover:bg-aegis-primary/80"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return children;
}
