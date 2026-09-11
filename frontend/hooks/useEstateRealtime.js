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
  unsubscribeFromSystemStatusUpdates,
  unsubscribeFromRobotUpdates,
  unsubscribeFromSensorReadings,
  unsubscribeFromDigitalTwinUpdates,
} from '../utils/socketClient';

const useEstateRealtime = (estateState) => {
  const { user, loading } = useCurrentUser();
  const [socketConnected, setSocketConnected] = useState(false);
  const [realtimeError, setRealtimeError] = useState(null);
  const [liveSystemStatus, setLiveSystemStatus] = useState(null);
  const [liveSensorReadings, setLiveSensorReadings] = useState([]);
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

    return () => {
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      socket.off('error', handleSocketError);
      unsubscribeFromSystemStatusUpdates();
      unsubscribeFromRobotUpdates();
      unsubscribeFromSensorReadings();
      unsubscribeFromDigitalTwinUpdates();
      disconnectSocket();
      setSocketConnected(false);
    };
  }, [user, loading]);

  return {
    socketConnected,
    realtimeError,
    liveSystemStatus,
    liveSensorReadings,
  };
};

export default useEstateRealtime;
