const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

/**
 * Authenticate an operator and retrieve a JWT session token.
 */
export const loginAPI = async (email, password) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // Send trimmed credentials to the backend
      body: JSON.stringify({ 
        email: email.trim().toLowerCase(), 
        password: password 
      }), 
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Authentication failed');
    }

    return await response.json(); 
  } catch (error) {
    console.error("API Error during login:", error);
    throw error;
  }
};

/**
 * Fetch specific Tenant (Estate) information using a Bearer token.
 */
export const getTenantInfo = async (token, tenantId = 1) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/tenants/${tenantId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`, // Crucial for Day 19 Security
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch tenant data');
    }

    return await response.json();
  } catch (error) {
    console.error("API Error fetching tenant:", error);
    throw error;
  }
};

export const getZones = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/zones`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    // THE FIX: Explicitly throw a 401 error
    if (response.status === 401) throw new Error('401 Unauthorized');
    if (!response.ok) throw new Error('Failed to fetch zones');
    
    return await response.json();
  } catch (error) {
    throw error;
  }
};

/**
 * NEW: Fetch all Sensors and their latest readings.
 * This connects the Live Telemetry card to your simulate_sensors.py script.
 */
export const getSensors = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/sensors`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    // THE FIX: Explicitly throw a 401 error
    if (response.status === 401) throw new Error('401 Unauthorized');
    if (!response.ok) throw new Error('Failed to fetch sensors');
    
    const data = await response.json();
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * NEW: Fetch Audit Logs.
 * This will populate the 'Recent Activity' feed with sensor registrations and data alerts.
 */
export const getAuditLogs = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/audit`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    // THE FIX: Explicitly throw a 401 error
    if (response.status === 401) throw new Error('401 Unauthorized');
    if (!response.ok) throw new Error('Failed to fetch audit logs');
    
    return await response.json();
  } catch (error) {
    throw error;
  }
};