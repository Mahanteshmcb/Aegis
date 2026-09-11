import React, { useState, useEffect, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Grid, Plane, Box, Sphere, Cylinder } from '@react-three/drei';
import * as THREE from 'three';
import { Video, Wifi, Wind, Radio, Eye, Eye2, Grid3X3, MapPin } from 'lucide-react';

// 3D Zone Representation
function Zone3D({ zone, isSelected, onClick }) {
  const meshRef = useRef();
  
  useFrame(() => {
    if (meshRef.current && isSelected) {
      meshRef.current.material.emissiveIntensity = Math.sin(Date.now() * 0.003) * 0.5 + 0.5;
    }
  });

  const statusColor = zone.status === 'secure' ? '#22c55e' : zone.status === 'warning' ? '#eab308' : '#ef4444';

  return (
    <Box 
      ref={meshRef}
      args={[zone.width || 5, 3, zone.depth || 5]}
      position={zone.position || [0, 1.5, 0]}
      onClick={onClick}
    >
      <meshStandardMaterial 
        color={statusColor}
        emissive={statusColor}
        emissiveIntensity={isSelected ? 1 : 0.3}
        transparent
        opacity={0.6}
        wireframe={false}
      />
    </Box>
  );
}

// 3D Sensor Representation
function Sensor3D({ sensor, isActive, onClick }) {
  const meshRef = useRef();
  
  useFrame(() => {
    if (meshRef.current && isActive) {
      meshRef.current.rotation.y += 0.02;
      meshRef.current.position.y += Math.sin(Date.now() * 0.005) * 0.01;
    }
  });

  const sensorTypeShapes = {
    'temperature': <Cylinder args={[0.3, 0.3, 0.8, 8]} />,
    'motion': <Sphere args={[0.4, 8, 8]} />,
    'humidity': <Box args={[0.4, 0.8, 0.4]} />,
    'pressure': <Sphere args={[0.35, 8, 8]} />,
    'camera': <Box args={[0.6, 0.4, 0.3]} />,
  };

  return (
    <group ref={meshRef} position={sensor.position || [0, 2, 0]} onClick={onClick}>
      {sensorTypeShapes[sensor.type] || <Sphere args={[0.3, 8, 8]} />}
      <meshStandardMaterial 
        color={isActive ? '#3b82f6' : '#6b7280'}
        emissive={isActive ? '#3b82f6' : '#000000'}
        emissiveIntensity={isActive ? 1 : 0}
        metalness={0.7}
        roughness={0.2}
      />
    </group>
  );
}

// 3D Robot/Asset Representation
function Robot3D({ robot, isActive, onClick }) {
  const meshRef = useRef();
  
  useFrame(() => {
    if (meshRef.current && isActive) {
      meshRef.current.rotation.z = (Date.now() * 0.002) % (Math.PI * 2);
    }
  });

  return (
    <group ref={meshRef} position={robot.position || [0, 0.5, 0]} onClick={onClick}>
      <Box args={[0.6, 0.4, 0.6]}>
        <meshStandardMaterial color={isActive ? '#f59e0b' : '#9ca3af'} />
      </Box>
      <Sphere args={[0.3, 8, 8]} position={[0, 0.4, 0]}>
        <meshStandardMaterial color={isActive ? '#fbbf24' : '#d1d5db'} />
      </Sphere>
    </group>
  );
}

// Main 3D Monitoring Scene
function MonitoringScene({ zones, sensors, robots, selectedObject, onSelectObject, viewMode }) {
  return (
    <group>
      {/* Ground Grid */}
      <Plane args={[50, 50]} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <meshStandardMaterial color="#111827" />
      </Plane>
      <Grid args={[50, 50]} cellSize={1} cellColor="#374151" sectionSize={5} sectionColor="#4b5563" fadeDistance={100} fadeStrength={1} />

      {/* Zones */}
      {zones.map((zone) => (
        <Zone3D
          key={zone.id}
          zone={zone}
          isSelected={selectedObject?.id === zone.id && selectedObject?.type === 'zone'}
          onClick={() => onSelectObject({ ...zone, type: 'zone' })}
        />
      ))}

      {/* Sensors */}
      {sensors.map((sensor) => (
        <Sensor3D
          key={sensor.id}
          sensor={sensor}
          isActive={selectedObject?.id === sensor.id && selectedObject?.type === 'sensor'}
          onClick={() => onSelectObject({ ...sensor, type: 'sensor' })}
        />
      ))}

      {/* Robots */}
      {robots.map((robot) => (
        <Robot3D
          key={robot.id}
          robot={robot}
          isActive={selectedObject?.id === robot.id && selectedObject?.type === 'robot'}
          onClick={() => onSelectObject({ ...robot, type: 'robot' })}
        />
      ))}

      {/* Lighting */}
      <ambientLight intensity={0.7} />
      <directionalLight position={[10, 20, 10]} intensity={1} />
      <pointLight position={[0, 5, 0]} intensity={0.5} />
    </group>
  );
}

// 3D Visualization Component
export default function Monitor3D({ zones = [], sensors = [], robots = [] }) {
  const [selectedObject, setSelectedObject] = useState(null);
  const [viewMode, setViewMode] = useState('3d'); // 3d, schematic, wireframe, heatmap, satellite

  const modes = [
    { name: '3D', value: '3d', icon: Eye },
    { name: 'Schematic', value: 'schematic', icon: Grid3X3 },
    { name: 'Wireframe', value: 'wireframe', icon: Radio },
    { name: 'Heatmap', value: 'heatmap', icon: Wind },
    { name: 'Satellite', value: 'satellite', icon: MapPin },
  ];

  const canvasProps = {
    gl: { antialias: true, powerPreference: 'high-performance' },
    onCreated: (state) => state.gl.setPixelRatio(Math.min(window.devicePixelRatio, 2)),
  };

  return (
    <div className="aegis-canvas-shell w-full h-full min-h-[360px] flex flex-col bg-slate-900">
      {/* View Mode Controls */}
      <div className="flex flex-wrap gap-2 p-4 bg-slate-800/50 border-b border-slate-700">
        {modes.map((mode) => {
          const Icon = mode.icon;
          return (
            <button
              key={mode.value}
              onClick={() => setViewMode(mode.value)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
                viewMode === mode.value
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <Icon size={16} />
              <span className="text-sm">{mode.name}</span>
            </button>
          );
        })}
      </div>

      {/* 3D Canvas */}
      <div className="aegis-monitor-canvas flex-1 min-h-[300px] relative">
        {viewMode === '3d' && (
          <Canvas camera={{ position: [15, 12, 15], fov: 50 }} {...canvasProps}>
            <MonitoringScene
              zones={zones}
              sensors={sensors}
              robots={robots}
              selectedObject={selectedObject}
              onSelectObject={setSelectedObject}
              viewMode={viewMode}
            />
            <OrbitControls />
          </Canvas>
        )}
        {viewMode === 'schematic' && (
          <div className="w-full h-full bg-slate-800 flex items-center justify-center text-slate-400">
            <Canvas camera={{ position: [0, 20, 0], fov: 50 }} {...canvasProps}>
              <MonitoringScene
                zones={zones}
                sensors={sensors}
                robots={robots}
                selectedObject={selectedObject}
                onSelectObject={setSelectedObject}
                viewMode={viewMode}
              />
            </Canvas>
          </div>
        )}
        {viewMode === 'wireframe' && (
          <Canvas camera={{ position: [15, 12, 15], fov: 50 }} {...canvasProps}>
            <MonitoringScene
              zones={zones}
              sensors={sensors}
              robots={robots}
              selectedObject={selectedObject}
              onSelectObject={setSelectedObject}
              viewMode={viewMode}
            />
            <OrbitControls />
          </Canvas>
        )}
        {viewMode === 'heatmap' && (
          <div className="w-full h-full bg-gradient-to-br from-blue-900 via-red-900 to-yellow-900 flex items-center justify-center">
            <div className="text-center text-white">
              <p className="text-2xl font-bold mb-2">🔥 Heatmap View</p>
              <p className="text-slate-300">Temperature/Activity Distribution</p>
            </div>
          </div>
        )}
        {viewMode === 'satellite' && (
          <Canvas camera={{ position: [0, 30, 0], fov: 50 }} {...canvasProps}>
            <MonitoringScene
              zones={zones}
              sensors={sensors}
              robots={robots}
              selectedObject={selectedObject}
              onSelectObject={setSelectedObject}
              viewMode={viewMode}
            />
          </Canvas>
        )}
      </div>

      {/* Selected Object Panel */}
      {selectedObject && (
        <div className="p-4 bg-slate-800/50 border-t border-slate-700">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400">Selected: {selectedObject.type.toUpperCase()}</p>
              <p className="text-lg font-semibold text-white">{selectedObject.name}</p>
              <div className="mt-2 grid grid-cols-3 gap-4 text-xs text-slate-300">
                {selectedObject.type === 'sensor' && (
                  <>
                    <div>Type: {selectedObject.sensor_type}</div>
                    <div>Status: {selectedObject.status}</div>
                    <div>Value: {selectedObject.value}</div>
                  </>
                )}
                {selectedObject.type === 'robot' && (
                  <>
                    <div>Battery: {selectedObject.battery}%</div>
                    <div>Status: {selectedObject.status}</div>
                    <div>Tasks: {selectedObject.active_tasks}</div>
                  </>
                )}
                {selectedObject.type === 'zone' && (
                  <>
                    <div>Status: {selectedObject.status}</div>
                    <div>Sensors: {selectedObject.sensor_count}</div>
                    <div>Security Level: {selectedObject.security_level}</div>
                  </>
                )}
              </div>
            </div>
            <button
              onClick={() => setSelectedObject(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
