import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aegis_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized: remove stored JWT and emit an application event
      try {
        localStorage.removeItem('aegis_token');
      } catch (e) {
        // ignore
      }
      try {
        window.dispatchEvent(new CustomEvent('aegis:unauthorized', { detail: { url: error.config?.url } }));
      } catch (e) {
        // fallback to a gentle redirect if events aren't available
        if (typeof window !== 'undefined') window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ========================
// ROBOT OPERATIONS
// ========================
export const robotAPI = {
  getAll: async (tenantId) => {
    const response = await api.get(`/robots?tenant_id=${tenantId}`);
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/robots/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/robots', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/robots/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/robots/${id}`);
  },

  sendHeartbeat: async (id, data) => {
    const response = await api.post(`/robots/${id}/heartbeat`, data);
    return response.data;
  },

  bulkAction: async (action, robotIds) => {
    const response = await api.post('/robots/bulk', { action, robot_ids: robotIds });
    return response.data;
  },
};

// ========================
// SENSOR OPERATIONS
// ========================
export const sensorAPI = {
  getAll: async (tenantId) => {
    const response = await api.get(`/sensors?tenant_id=${tenantId}`);
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/sensors/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/sensors', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/sensors/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/sensors/${id}`);
  },

  getData: async (id, timeRange = '24h') => {
    const response = await api.get(`/sensors/${id}/data?time_range=${timeRange}`);
    return response.data;
  },
};

// ========================
// ZONE OPERATIONS
// ========================
export const zoneAPI = {
  getAll: async (tenantId) => {
    const response = await api.get(`/zones?tenant_id=${tenantId}`);
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/zones/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/zones', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/zones/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/zones/${id}`);
  },

  getZoneStats: async (id) => {
    const response = await api.get(`/zones/${id}/stats`);
    return response.data;
  },
};

// ========================
// TASK OPERATIONS
// ========================
export const taskAPI = {
  getAll: async (tenantId) => {
    const response = await api.get(`/tasks?tenant_id=${tenantId}`);
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/tasks/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/tasks', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/tasks/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/tasks/${id}`);
  },

  cancel: async (id) => {
    const response = await api.post(`/tasks/${id}/cancel`);
    return response.data;
  },
};

// ========================
// USER OPERATIONS
// ========================
export const userAPI = {
  getAll: async (tenantId) => {
    const response = await api.get(`/users?tenant_id=${tenantId}`);
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/users/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/users', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/users/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/users/${id}`);
  },

  getCurrentUser: async () => {
    const response = await api.get('/users/me');
    return response.data;
  },
};

// ========================
// COMMUNICATION OPERATIONS
// ========================
export const communicationAPI = {
  getChannels: async (tenantId) => {
    const response = await api.get(`/communication/channels?tenant_id=${tenantId}`);
    return response.data;
  },

  createChannel: async (data) => {
    const response = await api.post('/communication/channels', data);
    return response.data;
  },

  updateChannelStatus: async (channelId, status) => {
    const response = await api.put(`/communication/channels/${channelId}`, { status });
    return response.data;
  },

  getStatus: async (tenantId) => {
    const response = await api.get(`/communication/status?tenant_id=${tenantId}`);
    return response.data;
  },
};

// ========================
// ALERT OPERATIONS
// ========================
export const alertAPI = {
  getAll: async (tenantId) => {
    const response = await api.get(`/alerts?tenant_id=${tenantId}`);
    return response.data;
  },

  getRules: async (tenantId) => {
    const response = await api.get(`/alert-rules?tenant_id=${tenantId}`);
    return response.data;
  },

  createRule: async (data) => {
    const response = await api.post('/alert-rules', data);
    return response.data;
  },

  updateRule: async (id, data) => {
    const response = await api.put(`/alert-rules/${id}`, data);
    return response.data;
  },

  deleteRule: async (id) => {
    await api.delete(`/alert-rules/${id}`);
  },

  acknowledgeAlert: async (alertId) => {
    const response = await api.post(`/alerts/${alertId}/acknowledge`);
    return response.data;
  },
};

// ========================
// ANALYTICS OPERATIONS
// ========================
export const analyticsAPI = {
  getSystemMetrics: async (tenantId, timeRange = '24h') => {
    const response = await api.get(`/analytics/system?tenant_id=${tenantId}&time_range=${timeRange}`);
    return response.data;
  },

  getRobotMetrics: async (robotId, timeRange = '24h') => {
    const response = await api.get(`/analytics/robots/${robotId}?time_range=${timeRange}`);
    return response.data;
  },

  getSensorMetrics: async (sensorId, timeRange = '24h') => {
    const response = await api.get(`/analytics/sensors/${sensorId}?time_range=${timeRange}`);
    return response.data;
  },

  getZoneMetrics: async (zoneId, timeRange = '24h') => {
    const response = await api.get(`/analytics/zones/${zoneId}?time_range=${timeRange}`);
    return response.data;
  },
};

export default api;
