import { useState, useCallback, useEffect } from 'react';

export const useEstateState = (initialData = {}) => {
  const [robots, setRobots] = useState(initialData.robots || []);
  const [sensors, setSensors] = useState(initialData.sensors || []);
  const [zones, setZones] = useState(initialData.zones || []);
  const [tasks, setTasks] = useState(initialData.tasks || []);
  const [users, setUsers] = useState(initialData.users || []);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState({});

  // Robot operations
  const addRobot = useCallback((robot) => {
    setRobots((prev) => [...prev, { id: Date.now(), ...robot }]);
  }, []);

  const updateRobot = useCallback((id, updates) => {
    setRobots((prev) => prev.map((r) => (r.id === id ? { ...r, ...updates } : r)));
  }, []);

  const deleteRobot = useCallback((id) => {
    setRobots((prev) => prev.filter((r) => r.id !== id));
  }, []);

  // Sensor operations
  const addSensor = useCallback((sensor) => {
    setSensors((prev) => [...prev, { id: Date.now(), ...sensor }]);
  }, []);

  const updateSensor = useCallback((id, updates) => {
    setSensors((prev) => prev.map((s) => (s.id === id ? { ...s, ...updates } : s)));
  }, []);

  const deleteSensor = useCallback((id) => {
    setSensors((prev) => prev.filter((s) => s.id !== id));
  }, []);

  // Zone operations
  const addZone = useCallback((zone) => {
    setZones((prev) => [...prev, { id: Date.now(), ...zone }]);
  }, []);

  const updateZone = useCallback((id, updates) => {
    setZones((prev) => prev.map((z) => (z.id === id ? { ...z, ...updates } : z)));
  }, []);

  const deleteZone = useCallback((id) => {
    setZones((prev) => prev.filter((z) => z.id !== id));
  }, []);

  // Task operations
  const addTask = useCallback((task) => {
    setTasks((prev) => [...prev, { id: Date.now(), ...task }]);
  }, []);

  const updateTask = useCallback((id, updates) => {
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, ...updates } : t)));
  }, []);

  const deleteTask = useCallback((id) => {
    setTasks((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Update metrics
  const updateMetrics = useCallback((newMetrics) => {
    setMetrics((prev) => ({ ...prev, ...newMetrics }));
  }, []);

  // Update sensor values (for real-time updates)
  const updateSensorValue = useCallback((sensorId, value) => {
    updateSensor(sensorId, { value });
  }, [updateSensor]);

  // Update robot position (for real-time updates)
  const updateRobotPosition = useCallback((robotId, position) => {
    updateRobot(robotId, { position });
  }, [updateRobot]);

  return {
    // Data
    robots,
    sensors,
    zones,
    tasks,
    users,
    selectedEntity,
    metrics,

    // State
    loading,
    error,
    setLoading,
    setError,
    setSelectedEntity,

    // Robot operations
    addRobot,
    updateRobot,
    deleteRobot,

    // Sensor operations
    addSensor,
    updateSensor,
    deleteSensor,
    updateSensorValue,

    // Zone operations
    addZone,
    updateZone,
    deleteZone,

    // Task operations
    addTask,
    updateTask,
    deleteTask,

    // Utility
    updateMetrics,
    updateRobotPosition,

    // Batch updates
    setRobots,
    setSensors,
    setZones,
    setTasks,
    setUsers,
  };
};

export default useEstateState;
