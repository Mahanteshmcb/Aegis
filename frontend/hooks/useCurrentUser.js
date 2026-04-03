import { useEffect, useState } from 'react';
import { getAuthToken } from '../utils/auth';
import { getCurrentUser } from '../utils/api';

export default function useCurrentUser() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    const loadUser = async () => {
      try {
        const profile = await getCurrentUser(token);
        setUser(profile);
      } catch (error) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  return { user, loading };
}
