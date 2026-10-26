import { useEffect, useState } from 'react';
import { clearAuthToken, getAuthToken, getRefreshToken, setAuthToken, setRefreshToken } from '../utils/auth';
import { getCurrentUser, refreshAuthToken } from '../utils/api';

export default function useCurrentUser() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => getAuthToken());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const activeToken = getAuthToken();
    setToken(activeToken);

    if (!activeToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    const loadUser = async () => {
      try {
        let profile;
        try {
          profile = await getCurrentUser(activeToken);
        } catch (error) {
          const refreshToken = getRefreshToken();
          if (!refreshToken) throw error;
          const refreshed = await refreshAuthToken(refreshToken);
          setAuthToken(refreshed.access_token);
          setRefreshToken(refreshed.refresh_token);
          setToken(refreshed.access_token);
          profile = await getCurrentUser(refreshed.access_token);
        }
        setUser(profile);
      } catch (error) {
        clearAuthToken();
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  return { user, loading, token };
}
