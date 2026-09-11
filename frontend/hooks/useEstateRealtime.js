import { useEffect, useRef, useState } from 'react';
import useCurrentUser from './useCurrentUser';
import { getAuthToken } from '../utils/auth';
import {
  initializeSocket,
  disconnectSocket,
  subscribeToSystemStatusUpdates,
  subscribeToRobotUpdates,
  subscribeToSensorReadings,
  subscribeToDigitalTwinUpdates,
  subscribeToDigitalTwinAlerts,
  unsubscribeFromSystemStatusUpdates,
  unsubscribeFromRobotUpdates,
  unsubscribeFromSensorReadings,
  unsubscribeFromDigitalTwinUpdates,
  unsubscribeFromDigitalTwinAlerts,
} from '../utils/socketClient';

const useEstateRealtime = (estateState) => {
  const { user, loading } = useCurrentUser();
  const [socketConnected, setSocketConnected] = useState(false);
  const [realtimeError, setRealtimeError] = useState(null);
  const [liveSystemStatus, setLiveSystemStatus] = useState(null);
  const [liveSensorReadings, setLiveSensorReadings] = useState([]);
  const [liveAlerts, setLiveAlerts] = useState([]);
  const [liveEvents, setLiveEvents] = useState([]);
  const estateStateRef = useRef(estateState);

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

    subscribeToSystemStatusUpdates((payload) => {
      if (!payload) return;

      const systems = Array.isArray(payload.systems) ? payload.systems : [];
      setLiveSystemStatus({
        ...payload,
        systems,
        timestamp: payload.timestamp || Date.now(),
      });

      if (systems.length) {
        const overallHealth = systems.reduce((acc, system) => acc + (Number(system.health_score) || 0), 0) / systems.length;
        estateStateRef.current?.updateMetrics?.({ systemHealth: Math.round(overallHealth) });
      }
    });

    subscribeToRobotUpdates((event) => {
      if (!event?.data) return;
      const data = event.data;
      estateStateRef.current?.setRobots?.((prev) => prev.map((robot) => {
        const match = String(robot.id) === String(data.robot_id) || String(robot.robot_id) === String(data.robot_id);
        return match ? { ...robot, ...data } : robot;
      }));
    });

    subscribeToSensorReadings((reading) => {
      const normalizedReading = {
        ...reading,
        value: reading.value ?? reading.value_raw ?? reading.payload?.value ?? reading.reading,
        timestamp: reading.timestamp || Date.now(),
      };

      setLiveSensorReadings((prev) => [normalizedReading, ...prev].slice(0, 20));
      setLiveEvents((previous) => [{
        id: `sensor-${normalizedReading.sensor_id}-${normalizedReading.timestamp}`,
        type: 'telemetry',
        message: `${normalizedReading.sensor_name || `Sensor ${normalizedReading.sensor_id}`} reported ${normalizedReading.value ?? 'a new value'}`,
        timestamp: normalizedReading.timestamp,
      }, ...previous].slice(0, 30));

      if (normalizedReading?.sensor_id !== undefined) {
        const sensorValue = normalizedReading.value;
        if (sensorValue !== undefined && sensorValue !== null) {
          estateStateRef.current?.updateSensorValue?.(normalizedReading.sensor_id, sensorValue);
        }
      }
    });

    subscribeToDigitalTwinUpdates((device) => {
      if (!device?.device_id && device?.id === undefined) return;

      const deviceId = device.device_id ?? device.id;
      const kind = device.kind || device.device_type;
      if (kind === 'sensor') {
        setLiveSensorReadings((prev) => [{
          sensor_id: deviceId,
          sensor_name: device.name,
          type: device.device_type,
          value: device.state?.value,
          unit: device.state?.unit,
          reading_status: device.state?.reading_status,
          thresholds: device.state?.thresholds,
          timestamp: device.last_updated || Date.now(),
        }, ...prev].slice(0, 20));
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
        id: `alert-${alert.device_id}-${alert.timestamp}`,
        type: alert.severity || 'warning',
        message: alert.message || `${alert.device_id} requires attention`,
        timestamp: alert.timestamp || Date.now(),
      }, ...previous].slice(0, 30));
    });

    return () => {
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      socket.off('error', handleSocketError);
      unsubscribeFromSystemStatusUpdates();
      unsubscribeFromRobotUpdates();
      unsubscribeFromSensorReadings();
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
