import { useEffect, useState } from 'react';
import useCurrentUser from './useCurrentUser';
import { getAuthToken } from '../utils/auth';
import {
  initializeSocket,
  disconnectSocket,
  subscribeToSystemStatusUpdates,
  subscribeToRobotUpdates,
  subscribeToSensorReadings,
  unsubscribeFromSystemStatusUpdates,
  unsubscribeFromRobotUpdates,
  unsubscribeFromSensorReadings,
} from '../utils/socketClient';

const useEstateRealtime = (estateState) => {
  const { user, loading } = useCurrentUser();
  const [socketConnected, setSocketConnected] = useState(false);
  const [realtimeError, setRealtimeError] = useState(null);
  const [liveSystemStatus, setLiveSystemStatus] = useState(null);
  const [liveSensorReadings, setLiveSensorReadings] = useState([]);

  useEffect(() => {
    if (loading || !user) {
      return undefined;
    }

    const token = getAuthToken();
    const socket = initializeSocket(token);

    socket.on('connect', () => {
      setSocketConnected(true);
      setRealtimeError(null);
    });

    socket.on('disconnect', () => {
      setSocketConnected(false);
    });

    socket.on('error', (error) => {
      console.error('Realtime socket error:', error);
      setRealtimeError(error?.message || 'Realtime connection error');
    });

    subscribeToSystemStatusUpdates((payload) => {
      if (!payload) return;
      setLiveSystemStatus(payload);
      if (payload.systems?.length) {
        const overallHealth = payload.systems.reduce((acc, system) => acc + (system.health_score || 0), 0) / payload.systems.length;
        estateState.updateMetrics({ systemHealth: Math.round(overallHealth) });
      }
    });

    subscribeToRobotUpdates((event) => {
      if (!event?.data) return;
      const data = event.data;
      estateState.setRobots((prev) => prev.map((robot) => {
        const match = String(robot.id) === String(data.robot_id) || String(robot.robot_id) === String(data.robot_id);
        return match ? { ...robot, ...data } : robot;
      }));
    });

    subscribeToSensorReadings((reading) => {
      setLiveSensorReadings((prev) => [reading, ...prev].slice(0, 20));
      if (reading?.sensor_id !== undefined) {
        estateState.updateSensorValue(reading.sensor_id, reading.value ?? reading.value_raw ?? reading.payload?.value);
      }
    });

    return () => {
      unsubscribeFromSystemStatusUpdates();
      unsubscribeFromRobotUpdates();
      unsubscribeFromSensorReadings();
      disconnectSocket();
      setSocketConnected(false);
    };
  }, [user, loading, estateState.setRobots, estateState.updateSensorValue, estateState.updateMetrics]);

  return {
    socketConnected,
    realtimeError,
    liveSystemStatus,
    liveSensorReadings,
  };
};

export default useEstateRealtime;
