const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const authHeaders = (token) => {
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
};

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

export const registerAPI = async (email, password, tenantId = 1) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.trim().toLowerCase(),
        password,
        tenant_id: tenantId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error during signup:', error);
    throw error;
  }
};

export const resetPasswordAPI = async (email) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: email.trim().toLowerCase() }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Reset password request failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error during reset password:', error);
    throw error;
  }
};

export const getCurrentUser = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch current user');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching current user:', error);
    throw error;
  }
};

export const refreshAuthToken = async (refreshToken) => {
  const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Session refresh failed');
  }

  return response.json();
};

export const getSystemHealthStatus = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/health`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Health check failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching health status:', error);
    throw error;
  }
};

export const createBackupSnapshot = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/robotics/sync/backups`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Backup snapshot creation failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error creating backup snapshot:', error);
    throw error;
  }
};

export const createDataSyncJob = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/robotics/sync/jobs`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Data sync job creation failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error creating data sync job:', error);
    throw error;
  }
};

export const completeDataSyncJob = async (token, syncId, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/robotics/sync/jobs/${syncId}/complete`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Data sync job completion failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error completing data sync job:', error);
    throw error;
  }
};

export const emergencyStop = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/robotics/emergency-stop`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Emergency stop failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error calling emergency stop:', error);
    throw error;
  }
};

// --- Day 65 frontend hooks ---
export const exportAuditCSV = async (token, params = {}) => {
  const url = new URL(`${API_URL}/api/v1/audit/export`);
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== null && url.searchParams.append(k, String(v)));
  const response = await fetch(url.toString(), { headers: authHeaders(token) });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to export audit logs');
  }
  const blob = await response.blob();
  return blob;
};

export const listSessions = async (token) => {
  const response = await fetch(`${API_URL}/api/v1/sessions`, { headers: authHeaders(token) });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to list sessions');
  }
  return await response.json();
};

export const revokeSession = async (token, sessionId) => {
  const response = await fetch(`${API_URL}/api/v1/sessions/${sessionId}/revoke`, {
    method: 'POST',
    headers: authHeaders(token),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to revoke session');
  }
  return await response.json();
};

export const bulkImportSensors = async (token, file) => {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(`${API_URL}/api/v1/sensors/bulk_import`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to import sensors');
  }
  return await response.json();
};
export const getWeatherForecast = async (token, params = {}) => {
  const url = new URL(`${API_URL}/api/v1/weather/local_forecast`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value));
    }
  });

  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch weather forecast');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching weather forecast:', error);
    throw error;
  }
};

export const getWeatherObservations = async (token, params = {}) => {
  const url = new URL(`${API_URL}/api/v1/weather/observations`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value));
    }
  });

  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch weather observations');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching weather observations:', error);
    throw error;
  }
};

export const getMaintenanceRecommendations = async (token, params = {}) => {
  const url = new URL(`${API_URL}/api/v1/weather/maintenance/recommendations`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value));
    }
  });

  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch maintenance recommendations');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching maintenance recommendations:', error);
    throw error;
  }
};

export const ingestWeatherObservation = async (token, observation) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/weather/observe`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(observation),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to ingest weather observation');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error ingesting weather observation:', error);
    throw error;
  }
};

export const requestOrganicCertification = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/audit/compliance/organic-certification/request`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to submit organic certification request');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error submitting certification request:', error);
    throw error;
  }
};

export const getOrganicCertificationStatus = async (token, tenantId) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/audit/compliance/organic-certification/${tenantId}`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch certification status');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching certification status:', error);
    throw error;
  }
};

export const fleetEmergencyStop = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/robotics/fleet/emergency-stop`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Fleet emergency stop failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error calling fleet emergency stop:', error);
    throw error;
  }
};

export const manualOverride = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/robotics/emergency/manual-override`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Manual override failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error calling manual override:', error);
    throw error;
  }
};

export const getPerimeterStatus = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/perimeter`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch perimeter status');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching perimeter status:', error);
    throw error;
  }
};

// --- Day 67: Telemetry Playback API hooks ---
export const createPlaybackSession = async (token, payload) => {
  const response = await fetch(`${API_URL}/api/v1/telemetry/playbacks`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create playback session');
  }
  return await response.json();
};

export const listPlaybackSessions = async (token) => {
  const response = await fetch(`${API_URL}/api/v1/telemetry/playbacks`, {
    method: 'GET',
    headers: authHeaders(token),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to list playback sessions');
  }
  return await response.json();
};

export const startPlaybackSession = async (token, sessionId) => {
  const response = await fetch(`${API_URL}/api/v1/telemetry/playbacks/${sessionId}/start`, {
    method: 'POST',
    headers: authHeaders(token),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to start playback session');
  }
  return await response.json();
};

export const stopPlaybackSession = async (token, sessionId) => {
  const response = await fetch(`${API_URL}/api/v1/telemetry/playbacks/${sessionId}/stop`, {
    method: 'POST',
    headers: authHeaders(token),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to stop playback session');
  }
  return await response.json();
};

export const exportPlaybackCSV = async (token, sessionId) => {
  const response = await fetch(`${API_URL}/api/v1/telemetry/playbacks/${sessionId}/export`, {
    method: 'GET',
    headers: authHeaders(token),
  });
  if (!response.ok) {
    const err = await response.text().catch(() => '');
    throw new Error(err || 'Failed to export playback CSV');
  }
  return await response.blob();
};

// --- Day 68: Notification rules ---
export const createNotificationRule = async (token, payload) => {
  const response = await fetch(`${API_URL}/api/v1/notifications/rules`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create notification rule');
  }
  return await response.json();
};

export const listNotificationRules = async (token) => {
  const response = await fetch(`${API_URL}/api/v1/notifications/rules`, {
    method: 'GET',
    headers: authHeaders(token),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to list notification rules');
  }
  return await response.json();
};

export const deleteNotificationRule = async (token, id) => {
  const response = await fetch(`${API_URL}/api/v1/notifications/rules/${id}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to delete notification rule');
  }
  return await response.json();
};

export const triggerPerimeterLockdown = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/perimeter/lockdown`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to activate perimeter lockdown');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error activating perimeter lockdown:', error);
    throw error;
  }
};

export const releasePerimeterLockdown = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/perimeter/release`, {
      method: 'POST',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to release perimeter lockdown');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error releasing perimeter lockdown:', error);
    throw error;
  }
};

export const verifyBiometricScan = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/access/biometric`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Biometric verification failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error verifying biometric scan:', error);
    throw error;
  }
};

export const getAccessControlLogs = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/access/logs`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch access control logs');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching access control logs:', error);
    throw error;
  }
};

export const getPatrolStatus = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/patrols/status`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch patrol status');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching patrol status:', error);
    throw error;
  }
};

export const startRoboticPatrol = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/patrols/start`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to start patrol');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error starting robotic patrol:', error);
    throw error;
  }
};

export const stopRoboticPatrol = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/patrols/stop`, {
      method: 'POST',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to stop patrol');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error stopping robotic patrol:', error);
    throw error;
  }
};

// --- Day 66: Scheduled Robotic Tasks ---
export const enqueueScheduledTask = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/robotics/schedule/enqueue`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to enqueue scheduled task');
    }
    return await response.json();
  } catch (error) {
    console.error('API Error enqueuing scheduled task:', error);
    throw error;
  }
};

export const getScheduledQueue = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/robotics/schedule/queue`, {
      method: 'GET',
      headers: authHeaders(token),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch scheduled queue');
    }
    return await response.json();
  } catch (error) {
    console.error('API Error fetching scheduled queue:', error);
    throw error;
  }
};

export const assignScheduledTasks = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/robotics/schedule/assign`, {
      method: 'POST',
      headers: authHeaders(token),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to assign scheduled tasks');
    }
    return await response.json();
  } catch (error) {
    console.error('API Error assigning scheduled tasks:', error);
    throw error;
  }
};

export const cancelScheduledTask = async (token, taskId) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/robotics/schedule/cancel/${taskId}`, {
      method: 'DELETE',
      headers: authHeaders(token),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to cancel scheduled task');
    }
    return await response.json();
  } catch (error) {
    console.error('API Error cancelling scheduled task:', error);
    throw error;
  }
};

export const getEvacuationStatus = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/evacuation`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch evacuation status');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching evacuation status:', error);
    throw error;
  }
};

export const triggerEvacuationProtocol = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/evacuation/trigger`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to trigger evacuation protocol');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error triggering evacuation protocol:', error);
    throw error;
  }
};

export const completeEvacuationProtocol = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/safety/evacuation/complete`, {
      method: 'POST',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to complete evacuation protocol');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error completing evacuation protocol:', error);
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
    if (response.status === 401) throw new Error('401 Unauthorized');
    if (!response.ok) throw new Error('Failed to fetch sensors');
    
    const data = await response.json();
    return data;
  } catch (error) {
    throw error;
  }
};

export const observeSensorTelemetry = async (token, sensor) => {
  if (!sensor || !sensor.sensor_id || !sensor.value) {
    throw new Error('Sensor telemetry is missing required fields');
  }

  const payload = {
    tenant_id: sensor.tenant_id || 1,
    zone_id: sensor.zone_id,
    sensor_id: sensor.sensor_id,
    timestamp: sensor.timestamp || new Date().toISOString(),
    temp_c: undefined,
    humidity_percent: undefined,
    wind_m_s: undefined,
    precip_mm: undefined,
    pressure_hpa: undefined,
  };

  const unit = (sensor.unit || '').toLowerCase();
  const value = Number(sensor.value);

  if (unit.includes('c') || unit.includes('temperature') || unit.includes('deg')) {
    payload.temp_c = value;
  } else if (unit.includes('%') || unit.includes('humidity')) {
    payload.humidity_percent = value;
  } else if (unit.includes('m/s') || unit.includes('wind')) {
    payload.wind_m_s = value;
  } else if (unit.includes('mm') || unit.includes('rain') || unit.includes('precip')) {
    payload.precip_mm = value;
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/weather/observe`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to ingest sensor telemetry as weather observation');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error ingesting sensor telemetry as weather observation:', error);
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

export const getEnergyStatus = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/energy/status`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch energy status');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching energy status:', error);
    throw error;
  }
};

export const getEnergyOverview = async (token, params = {}) => {
  const url = new URL(`${API_URL}/api/v1/energy/overview`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value));
    }
  });

  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch energy overview');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching energy overview:', error);
    throw error;
  }
};

export const getEnergyPolicy = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/energy/policy`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      return {};
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching energy policy:', error);
    return {};
  }
};

export const setEnergyPolicy = async (token, policy) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/energy/policy`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(policy),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to set policy');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error setting energy policy:', error);
    throw error;
  }
};

export const getSmartEnergySchedule = async (token, params = {}) => {
  const url = new URL(`${API_URL}/api/v1/energy/smart_schedule`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value));
    }
  });

  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch smart energy schedule');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching smart energy schedule:', error);
    throw error;
  }
};

// --- WATER MANAGEMENT API ---

export const getWaterCollectionSystems = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/water/collection`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch water collection systems');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching water collection systems:', error);
    throw error;
  }
};

export const createWaterCollectionSystem = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/water/collection`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create water collection system');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error creating water collection system:', error);
    throw error;
  }
};

export const getWaterPurificationUnits = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/water/purification`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch purification units');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching purification units:', error);
    throw error;
  }
};

export const createWaterPurificationUnit = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/water/purification`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create purification unit');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error creating purification unit:', error);
    throw error;
  }
};

export const getIrrigationSystems = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/water/irrigation`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch irrigation systems');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching irrigation systems:', error);
    throw error;
  }
};

export const createIrrigationSystem = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/water/irrigation`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create irrigation system');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error creating irrigation system:', error);
    throw error;
  }
};

export const recordWaterQualityReading = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/water/quality`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to record water quality reading');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error recording water quality reading:', error);
    throw error;
  }
};

export const getWaterQualityReadings = async (token, location) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/water/quality/${location}`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch water quality readings');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching water quality readings:', error);
    throw error;
  }
};

export const getWaterRecyclingLoops = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/water/recycling`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch water recycling loops');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching water recycling loops:', error);
    throw error;
  }
};

export const createWaterRecyclingLoop = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/water/recycling`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create water recycling loop');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error creating water recycling loop:', error);
    throw error;
  }
};

// --- WASTE MANAGEMENT API ---

export const getWasteContainers = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/containers`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch waste containers');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching waste containers:', error);
    throw error;
  }
};

export const createWasteContainer = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/containers`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create waste container');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error creating waste container:', error);
    throw error;
  }
};

export const recordWasteSorting = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/sorting`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to record waste sorting');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error recording waste sorting:', error);
    throw error;
  }
};

export const getWasteSortingLogs = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/sorting`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch waste sorting logs');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching waste sorting logs:', error);
    throw error;
  }
};

export const createCompostingProcess = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/composting`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create composting process');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error creating composting process:', error);
    throw error;
  }
};

export const getCompostingProcesses = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/composting`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch composting processes');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching composting processes:', error);
    throw error;
  }
};

export const createRecyclingProcess = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/recycling`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create recycling process');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error creating recycling process:', error);
    throw error;
  }
};

export const getRecyclingProcesses = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/recycling`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch recycling processes');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching recycling processes:', error);
    throw error;
  }
};

export const createHazardousWasteStorage = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/hazardous`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create hazardous waste storage');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error creating hazardous waste storage:', error);
    throw error;
  }
};

export const getHazardousWasteStorage = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/hazardous`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch hazardous waste storage');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching hazardous waste storage:', error);
    throw error;
  }
};

export const logWasteProcessing = async (token, payload) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/processing`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to log waste processing');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error logging waste processing:', error);
    throw error;
  }
};

export const getWasteMetrics = async (token) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/waste/metrics`, {
      method: 'GET',
      headers: authHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch waste metrics');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error fetching waste metrics:', error);
    throw error;
  }
};
