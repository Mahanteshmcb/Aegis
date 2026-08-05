import io from 'socket.io-client';

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const SOCKET_PATH = process.env.NEXT_PUBLIC_SOCKET_PATH || '/socket.io';

let socket = null;

export const initializeSocket = (token) => {
  if (socket?.connected) {
    return socket;
  }

  socket = io(SOCKET_URL, {
    path: SOCKET_PATH,
    transports: ['polling'],
    upgrade: false,
    auth: {
      token,
    },
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5,
  });

  socket.on('connect', () => {
    console.log('✓ WebSocket connected');
  });

  socket.on('disconnect', () => {
    console.log('✗ WebSocket disconnected');
  });

  socket.on('error', (error) => {
    console.error('WebSocket error:', error);
  });

  return socket;
};

export const getSocket = () => {
  return socket;
};

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};

// ========================
// REAL-TIME EVENT HANDLERS
// ========================

export const subscribeToRobotUpdates = (callback) => {
  if (!socket) return;

  socket.on('robot:position', (data) => {
    callback({
      type: 'robot:position',
      data,
    });
  });

  socket.on('robot:status', (data) => {
    callback({
      type: 'robot:status',
      data,
    });
  });

  socket.on('robot:battery', (data) => {
    callback({
      type: 'robot:battery',
      data,
    });
  });
};

export const subscribeToSensorUpdates = (callback) => {
  if (!socket) return;

  socket.on('sensor:data', (data) => {
    callback({
      type: 'sensor:data',
      data,
    });
  });

  socket.on('sensor:alert', (data) => {
    callback({
      type: 'sensor:alert',
      data,
    });
  });
};

export const subscribeToSystemAlerts = (callback) => {
  if (!socket) return;

  socket.on('system:alert', (data) => {
    callback({
      type: 'system:alert',
      data,
    });
  });

  socket.on('system:status', (data) => {
    callback({
      type: 'system:status',
      data,
    });
  });
};

export const subscribeToSystemStatusUpdates = (callback) => {
  if (!socket) return;

  socket.on('systemStatus:update', (data) => {
    callback(data);
  });
};

export const subscribeToSensorReadings = (callback) => {
  if (!socket) return;

  socket.on('sensor:reading', (data) => {
    callback(data);
  });
};

export const unsubscribeFromSystemStatusUpdates = () => {
  if (!socket) return;
  socket.off('systemStatus:update');
};

export const unsubscribeFromSensorReadings = () => {
  if (!socket) return;
  socket.off('sensor:reading');
};

export const subscribeToCommunicationUpdates = (callback) => {
  if (!socket) return;

  socket.on('communication:status', (data) => {
    callback({
      type: 'communication:status',
      data,
    });
  });

  socket.on('communication:connection', (data) => {
    callback({
      type: 'communication:connection',
      data,
    });
  });
};

export const subscribeToZoneUpdates = (callback) => {
  if (!socket) return;

  socket.on('zone:activity', (data) => {
    callback({
      type: 'zone:activity',
      data,
    });
  });
};

// ========================
// EMIT FUNCTIONS
// ========================

export const emitRobotCommand = (robotId, command, params = {}) => {
  if (!socket) return;
  socket.emit('robot:command', {
    robotId,
    command,
    params,
  });
};

export const emitTaskAssignment = (robotId, taskId) => {
  if (!socket) return;
  socket.emit('task:assign', {
    robotId,
    taskId,
  });
};

export const emitEmergencyStop = () => {
  if (!socket) return;
  socket.emit('system:emergency-stop');
};

// ========================
// UNSUBSCRIBE FUNCTIONS
// ========================

export const unsubscribeFromRobotUpdates = () => {
  if (!socket) return;
  socket.off('robot:position');
  socket.off('robot:status');
  socket.off('robot:battery');
};

export const unsubscribeFromSensorUpdates = () => {
  if (!socket) return;
  socket.off('sensor:data');
  socket.off('sensor:alert');
};

export const unsubscribeFromSystemAlerts = () => {
  if (!socket) return;
  socket.off('system:alert');
  socket.off('system:status');
};

export const unsubscribeFromCommunicationUpdates = () => {
  if (!socket) return;
  socket.off('communication:status');
  socket.off('communication:connection');
};

export const unsubscribeFromZoneUpdates = () => {
  if (!socket) return;
  socket.off('zone:activity');
};

export default {
  initializeSocket,
  getSocket,
  disconnectSocket,
  subscribeToRobotUpdates,
  subscribeToSensorUpdates,
  subscribeToSystemAlerts,
  subscribeToSystemStatusUpdates,
  subscribeToSensorReadings,
  subscribeToCommunicationUpdates,
  subscribeToZoneUpdates,
  emitRobotCommand,
  emitTaskAssignment,
  emitEmergencyStop,
  unsubscribeFromRobotUpdates,
  unsubscribeFromSensorUpdates,
  unsubscribeFromSystemAlerts,
  unsubscribeFromSystemStatusUpdates,
  unsubscribeFromSensorReadings,
  unsubscribeFromCommunicationUpdates,
  unsubscribeFromZoneUpdates,
};
