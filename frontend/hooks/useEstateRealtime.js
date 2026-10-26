import { useEffect, useRef, useState } from 'react';
import useCurrentUser from './useCurrentUser';
import { getAuthToken } from '../utils/auth';
import {
  initializeSocket,
  disconnectSocket,
  subscribeToDigitalTwinUpdates,
  subscribeToDigitalTwinAlerts,
  unsubscribeFromDigitalTwinUpdates,
  unsubscribeFromDigitalTwinAlerts,
} from '../utils/socketClient';

const summarizeDevices = (devices) => {
  const grouped = new Map();
  devices.forEach((device) => {
    const groupName = device.device_type || device.kind || 'other';
    const group = grouped.get(groupName) || [];
    group.push(device);
    grouped.set(groupName, group);
  });

  const systems = Array.from(grouped, ([name, assets]) => {
    const scores = assets.map((device) => {
      const status = device.state?.reading_status || device.status;
      if (status === 'critical' || status === 'offline' || status === 'error') return 0;
      if (status === 'warning') return 60;
      return 100;
    });
    const healthScore = Math.round(scores.reduce((total, score) => total + score, 0) / scores.length);
    return {
      name,
      asset_count: assets.length,
      health_score: healthScore,
      status: healthScore < 60 ? 'critical' : healthScore < 100 ? 'warning' : 'healthy',
    };
  });
  const healthScore = systems.length
    ? Math.round(systems.reduce((total, system) => total + system.health_score, 0) / systems.length)
    : 100;
  return { systems, health_score: healthScore };
};

const useEstateRealtime = (estateState) => {
  const { user, loading } = useCurrentUser();
  const [socketConnected, setSocketConnected] = useState(false);
  const [realtimeError, setRealtimeError] = useState(null);
  const [liveSystemStatus, setLiveSystemStatus] = useState(null);
  const [liveSensorReadings, setLiveSensorReadings] = useState([]);
  const [liveAlerts, setLiveAlerts] = useState([]);
  const [liveEvents, setLiveEvents] = useState([]);
  const estateStateRef = useRef(estateState);
  const liveDevicesRef = useRef(new Map());

  useEffect(() => {
    estateStateRef.current = estateState;
  }, [estateState]);

  useEffect(() => {
    if (loading || !user) {
      return undefined;
    }

    const token = getAuthToken();
    const socket = initializeSocket(token);

    const handleConnect = () => {
      setSocketConnected(true);
      setRealtimeError(null);
    };

    const handleDisconnect = () => {
      setSocketConnected(false);
    };

    const handleSocketError = (error) => {
      console.error('Realtime socket error:', error);
      setRealtimeError(error?.message || 'Realtime connection error');
    };

    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);
    socket.on('error', handleSocketError);

    subscribeToDigitalTwinUpdates((device) => {
      if (!device?.device_id && device?.id === undefined) return;

      const deviceId = device.device_id ?? device.id;
      const kind = device.kind || device.device_type;
      liveDevicesRef.current.set(String(deviceId), device);
      const summary = summarizeDevices(Array.from(liveDevicesRef.current.values()));
      setLiveSystemStatus({
        ...summary,
        timestamp: device.last_updated || Date.now(),
      });
      estateStateRef.current?.updateMetrics?.({ systemHealth: summary.health_score });
      if (kind === 'sensor') {
        const reading = {
          sensor_id: deviceId,
          sensor_name: device.name,
          type: device.device_type,
          value: device.state?.value,
          unit: device.state?.unit,
          reading_status: device.state?.reading_status,
          thresholds: device.state?.thresholds,
          timestamp: device.last_updated || Date.now(),
        };
        setLiveSensorReadings((prev) => [reading, ...prev].slice(0, 20));
        if (reading.value !== undefined && reading.value !== null) {
          estateStateRef.current?.updateSensorValue?.(deviceId, reading.value);
        }
      }
      setLiveEvents((previous) => [{
        id: `device-${deviceId}-${device.last_updated || Date.now()}`,
        type: 'device_update',
        message: `${device.name || deviceId} state updated`,
        timestamp: device.last_updated || Date.now(),
      }, ...previous].slice(0, 30));
      const collection = kind === 'robot' ? 'setRobots' : kind === 'sensor' ? 'setSensors' : null;
      if (!collection) return;

      estateStateRef.current?.[collection]?.((items) => items.map((item) => {
        const itemId = item.device_id ?? item.id ?? item.robot_id ?? item.sensor_id;
        return String(itemId) === String(deviceId)
          ? {
            ...item,
            ...device,
            id: item.id ?? device.id ?? deviceId,
            position: device.position || item.position,
            value: device.state?.value ?? item.value,
            status: device.status || item.status,
          }
          : item;
      }));
    });

    subscribeToDigitalTwinAlerts((alert) => {
      if (!alert?.device_id) return;
      setLiveAlerts((previous) => [alert, ...previous].slice(0, 20));
      setLiveEvents((previous) => [{
        id: alert.event_id || `alert-${alert.device_id}-${alert.timestamp}`,
        type: alert.severity || 'warning',
        message: alert.message || `${alert.device_id} requires attention`,
        timestamp: alert.timestamp || Date.now(),
      }, ...previous].slice(0, 30));
    });
    const handleAlertCleared = (alert) => {
      if (!alert?.device_id) return;
      setLiveAlerts((previous) => previous.filter((item) => (
        alert.event_id ? item.event_id !== alert.event_id : item.device_id !== alert.device_id
      )));
      setLiveEvents((previous) => [{
        id: `cleared-${alert.event_id || alert.device_id}-${alert.timestamp}`,
        type: 'normal',
        message: alert.message || `${alert.device_id} returned to normal`,
        timestamp: alert.timestamp || Date.now(),
      }, ...previous].slice(0, 30));
    };
    socket.on('digital_twin:alert_cleared', handleAlertCleared);

    return () => {
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      socket.off('error', handleSocketError);
      socket.off('digital_twin:alert_cleared', handleAlertCleared);
      unsubscribeFromDigitalTwinUpdates();
      unsubscribeFromDigitalTwinAlerts();
      disconnectSocket();
      setSocketConnected(false);
    };
  }, [user, loading]);

  return {
    socketConnected,
    realtimeError,
    liveSystemStatus,
    liveSensorReadings,
    liveAlerts,
    liveEvents,
  };
};

export default useEstateRealtime;
