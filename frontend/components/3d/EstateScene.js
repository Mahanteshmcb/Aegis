import React, { useRef, useState, useEffect, Suspense, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { Box3, Vector3 } from 'three';

const finiteNumber = (value, fallback = 0) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
};

const normalizeVector3 = (value, fallback = [0, 0, 0]) => {
  const safeFallback = [0, 1, 2].map((index) => finiteNumber(fallback[index], 0));

  if (!Array.isArray(value) && (!value || typeof value !== 'object')) {
    return safeFallback;
  }

  return [0, 1, 2].map((index) => {
    const axis = ['x', 'y', 'z'][index];
    const raw = Array.isArray(value) ? value[index] : value[axis];
    const fallbackValue = safeFallback[index] ?? 0;
    return finiteNumber(raw, fallbackValue);
  });
};

const normalizeBuildingSize = (value) => normalizeVector3(value, [6, 2, 6]).map((item, index) => (
  index === 1 ? Math.max(item, 0.2) : Math.max(Math.abs(item), 0.2)
));

const normalizeEntityPosition = (value) => normalizeVector3(value, [0, 0, 0]);
const normalizeEntitySize = (value) => normalizeVector3(value, [1, 1, 1]);

const normalizeDisplayEntities = (items, fallbackSize) => {
  const seen = new Set();
  return (Array.isArray(items) ? items : []).reduce((result, item, index) => {
    const id = String(item?.id ?? item?.device_id ?? `${fallbackSize}-${index}`);
    if (seen.has(id)) return result;
    seen.add(id);
    result.push({
      ...item,
      id,
      position: normalizeEntityPosition(item?.position),
      ...(fallbackSize === 'zone' ? { size: normalizeBuildingSize(item?.size) } : {}),
    });
    return result;
  }, []);
};

function AssetModel({ url, scale, rotation = [0, 0, 0] }) {
  const { scene } = useGLTF(url);
  const model = useMemo(() => {
    const clone = scene.clone(true);
    const bounds = new Box3().setFromObject(clone);
    const size = bounds.getSize(new Vector3());
    const largestDimension = Math.max(size.x, size.y, size.z, 0.001);
    clone.scale.setScalar(1.2 / largestDimension);
    return clone;
  }, [scene]);
  return <primitive object={model} scale={scale} rotation={rotation} dispose={null} />;
}

// Building Structure Component
function Building({ position, size, color, name, spatialStatus, lengthUnit, selected, onClick }) {
  const [hovered, setHovered] = useState(false);
  const safePosition = normalizeEntityPosition(position);
  const safeSize = normalizeBuildingSize(size);
  const wallHeight = Math.min(Math.max(safeSize[1], 3), 6);
  const wallThickness = Math.max(Math.min(safeSize[0], safeSize[2]) * 0.025, 0.35);
  const wallColor = selected ? '#5eead4' : hovered ? '#67e8f9' : color;

  return (
    <group position={safePosition}>
      {selected && (
        <mesh position={[0, 0.18, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[Math.max(safeSize[0], safeSize[2]) * 0.68, Math.max(safeSize[0], safeSize[2]) * 0.7, 4]} />
          <meshBasicMaterial color="#fef08a" transparent opacity={0.9} side={THREE.DoubleSide} />
        </mesh>
      )}

      <mesh position={[0, 0.08, 0]} onClick={onClick} onPointerEnter={() => setHovered(true)} onPointerLeave={() => setHovered(false)} receiveShadow>
        <boxGeometry args={[safeSize[0], 0.16, safeSize[2]]} />
        <meshStandardMaterial color={selected ? '#1d6560' : hovered ? '#356d55' : '#284d3b'} roughness={0.95} metalness={0.02} transparent opacity={selected ? 0.14 : 0.06} depthWrite={false} />
      </mesh>
      {[
        { position: [0, wallHeight / 2, -safeSize[2] / 2], size: [safeSize[0], wallHeight, wallThickness] },
        { position: [0, wallHeight / 2, safeSize[2] / 2], size: [safeSize[0], wallHeight, wallThickness] },
        { position: [-safeSize[0] / 2, wallHeight / 2, 0], size: [wallThickness, wallHeight, safeSize[2]] },
        { position: [safeSize[0] / 2, wallHeight / 2, 0], size: [wallThickness, wallHeight, safeSize[2]] },
      ].map((wall, index) => <mesh key={index} position={wall.position} onClick={onClick} castShadow receiveShadow>
        <boxGeometry args={wall.size} />
        <meshStandardMaterial color={wallColor} transparent opacity={selected ? 0.28 : hovered ? 0.2 : 0.1} roughness={0.72} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>)}
      <Text position={[0, 0.35, -safeSize[2] * 0.34]} fontSize={Math.min(Math.max(safeSize[0] * 0.055, 1.4), 3.5)} color="#e2f3e9" anchorX="center" anchorY="middle" outlineWidth={0.035} outlineColor="#102019">
        {`${name || 'Estate zone'} · ${spatialStatus === 'surveyed' ? 'SURVEYED' : 'INFERRED'} · ${lengthUnit || 'm'}`}
      </Text>
    </group>
  );
}

// Robot Component
function Robot({ position, status, state = {}, selected, onClick }) {
  const groupRef = useRef();
  const armRef = useRef();
  const robotTime = useRef(0);
  const safePosition = normalizeEntityPosition(position);
  const activity = String(state.activity || 'stationary').toLowerCase();
  const moving = ['patrolling', 'moving', 'working', 'navigating'].includes(activity);

  useFrame((state, delta) => {
    robotTime.current += delta;
    if (groupRef.current) {
      groupRef.current.position.set(...safePosition);
      groupRef.current.rotation.z = 0;
    }
    if (armRef.current) {
      armRef.current.rotation.z = moving ? Math.sin(robotTime.current * 3.2) * 0.18 : 0;
      armRef.current.rotation.x = moving ? Math.cos(robotTime.current * 1.8) * 0.1 : 0;
    }
  });

  const statusColor = status === 'offline' ? '#64748b'
    : status === 'critical' || status === 'error' ? '#ef4444'
      : status === 'warning' ? '#f59e0b'
        : status === 'charging' ? '#FF9500'
          : '#34C759';

  return (
    <group ref={groupRef} position={safePosition} onClick={onClick} onPointerDown={onClick}>
      {selected && (
        <mesh scale={[1.4, 1.4, 1.4]} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.55, 0.08, 16, 100]} />
          <meshBasicMaterial color="#ff66ff" transparent opacity={0.4} />
        </mesh>
      )}

      <group scale={0.42}>
        <mesh castShadow receiveShadow onClick={onClick} onPointerDown={onClick}>
          <cylinderGeometry args={[0.55, 0.72, 1.1, 18]} />
          <meshPhysicalMaterial color={selected ? '#ff66ff' : '#0af0ff'} emissive={selected ? '#ff66ff' : statusColor} emissiveIntensity={selected ? 0.8 : 0.4} roughness={0.15} metalness={0.85} />
        </mesh>
        <mesh position={[0, 0.82, 0]} castShadow receiveShadow>
          <sphereGeometry args={[0.48, 20, 20]} />
          <meshStandardMaterial color="#dbeafe" emissive={statusColor} emissiveIntensity={0.18} metalness={0.12} roughness={0.25} />
        </mesh>
        <mesh position={[0.55, 0.82, 0.05]} castShadow>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshBasicMaterial color="#f8fafc" transparent opacity={0.9} />
        </mesh>
      </group>

      <group ref={armRef} position={[0.25, 0.05, 0]}> 
        <mesh castShadow>
          <boxGeometry args={[0.08, 0.3, 0.08]} />
          <meshStandardMaterial color="#dbeafe" metalness={0.45} roughness={0.18} />
        </mesh>
        <mesh position={[0, 0.18, 0]} castShadow>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#fde68a" emissive="#facc15" emissiveIntensity={1.1} metalness={0.2} roughness={0.1} />
        </mesh>
      </group>

      <group position={[0, -0.24, 0]}> 
        {[-0.26, 0.26].map((x) => (
          <mesh key={x} position={[x, 0, 0]} castShadow>
            <cylinderGeometry args={[0.12, 0.12, 0.08, 16]} />
            <meshPhysicalMaterial color="#1f2937" roughness={0.35} metalness={0.2} />
          </mesh>
        ))}
      </group>

      <mesh position={[0.55, 0.18, 0]}>
        <sphereGeometry args={[0.09, 16, 16]} />
        <meshBasicMaterial color={statusColor} transparent opacity={0.95} />
      </mesh>
    </group>
  );
}

// Sensor Node Component
function SensorNode({ position, type, value, unit, readingStatus, name, selected, onClick }) {
  const meshRef = useRef();
  const ringRef = useRef();
  const sensorTime = useRef(0);
  const safePosition = normalizeEntityPosition(position);

  useFrame((state, delta) => {
    if (!meshRef.current) return;
    sensorTime.current += delta;
    const pulse = 1 + Math.sin(sensorTime.current * 2.8) * 0.12;
    const scale = selected ? 1.3 * pulse : 1.0 * pulse;
    meshRef.current.scale.set(scale, scale, scale);
    if (ringRef.current) {
      ringRef.current.rotation.z += delta * 0.7;
      ringRef.current.material.opacity = selected ? 0.7 : 0.35;
    }
  });

  const sensorColors = {
    temperature: '#FF6B6B',
    humidity: '#4ECDC4',
    pressure: '#45B7D1',
    light: '#FFD93D',
    motion: '#FF6B9D',
  };

  const color = sensorColors[type] || '#00ffff';
  const attention = readingStatus === 'warning' || readingStatus === 'critical';

  return (
    <group position={safePosition} onClick={onClick} onPointerDown={onClick}>
      {selected && (
        <mesh ref={ringRef} scale={[1.5, 1.5, 1.5]} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.32, 0.045, 16, 100]} />
          <meshBasicMaterial color="#7dd3fc" transparent opacity={0.5} />
        </mesh>
      )}
      <group ref={meshRef} scale={0.7}>
        <mesh castShadow receiveShadow onClick={onClick} onPointerDown={onClick}>
          <icosahedronGeometry args={[0.38, 1]} />
          <meshPhysicalMaterial color={selected ? '#ff66ff' : color} emissive={selected ? '#ff66ff' : color} emissiveIntensity={selected ? 0.9 : 0.65} metalness={0.45} roughness={0.1} />
        </mesh>
      </group>
      <mesh position={[0, -0.35, 0]}>
        <cylinderGeometry args={[0.04, 0.04, 0.22, 12]} />
        <meshStandardMaterial color="#0f172a" roughness={0.5} metalness={0.2} />
      </mesh>
      <mesh position={[0, -0.5, 0]}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshBasicMaterial color={color} transparent opacity={0.9} />
      </mesh>
      {(selected || attention) && (
        <Text position={[0, 0.95, 0]} fontSize={0.3} color={readingStatus === 'critical' ? '#fecaca' : readingStatus === 'warning' ? '#fde68a' : '#e2e8f0'} anchorX="center" anchorY="bottom" outlineWidth={0.025} outlineColor="#020617">
          {`${name || type}: ${value ?? 'No reading'}${value !== undefined && value !== null && unit ? ` ${unit}` : ''}${attention ? ` · ${readingStatus.toUpperCase()}` : ''}`}
        </Text>
      )}
    </group>
  );
}

// Connection Lines Component
function ConnectionLines({ robots, sensors }) {
  const getBeamTransform = (from, to) => {
    const safeFrom = normalizeEntityPosition(from);
    const safeTo = normalizeEntityPosition(to);
    const start = new THREE.Vector3(...safeFrom);
    const end = new THREE.Vector3(...safeTo);
    const direction = new THREE.Vector3().subVectors(end, start);
    const length = direction.length();
    const midpoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
    const orientation = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      direction.clone().normalize()
    );
    return { midpoint, orientation, length };
  };

  return (
    <group>
      {robots.map((robot, i) => (
        sensors.map((sensor, j) => {
          const robotPosition = normalizeEntityPosition(robot.position);
          const sensorPosition = normalizeEntityPosition(sensor.position);
          const distance = Math.hypot(
            robotPosition[0] - sensorPosition[0],
            robotPosition[2] - sensorPosition[2]
          );

          if (distance < 10) {
            const { midpoint, orientation, length } = getBeamTransform(robotPosition, sensorPosition);
            return (
              <mesh key={`${i}-${j}`} position={midpoint} quaternion={orientation}>
                <cylinderGeometry args={[0.03, 0.03, Math.max(length, 0.1), 8]} />
                <meshStandardMaterial color="#35f2ff" transparent opacity={0.18} emissive="#35f2ff" emissiveIntensity={0.3} />
              </mesh>
            );
          }
          return null;
        }))
      )}
    </group>
  );
}

function CoverageZone({ zone, selected, onClick }) {
  const safePosition = normalizeEntityPosition(zone.position);
  const safeSize = normalizeEntitySize(zone.size || [10, 2, 10]);
  const color = zone.color || '#38bdf8';

  return (
    <group position={safePosition}>
      <mesh position={[0, 0.19, 0]} onClick={onClick} receiveShadow>
        <boxGeometry args={[safeSize[0] * 0.96, 0.04, safeSize[2] * 0.96]} />
        <meshStandardMaterial color={color} transparent opacity={selected ? 0.09 : 0.025} roughness={1} depthWrite={false} />
      </mesh>
    </group>
  );
}

function DeviceStatusRing({ position, status, color, selected }) {
  const ringRef = useRef();
  const safePosition = normalizeEntityPosition(position);

  useFrame((state) => {
    if (!ringRef.current) return;
    ringRef.current.rotation.z += 0.015;
    ringRef.current.material.opacity = selected ? 0.9 : 0.54;
  });

  const statusMap = {
    active: '#34d399',
    charging: '#fbbf24',
    idle: '#60a5fa',
    warning: '#f87171',
    critical: '#ef4444',
    normal: '#34d399',
    online: '#34d399',
    offline: '#64748b',
    error: '#ef4444',
    secure: '#a78bfa',
    default: '#a5f3fc',
  };

  const ringColor = statusMap[status] || color || '#a5f3fc';

  return (
    <group position={safePosition}>
      <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.8, 0.08, 16, 80]} />
        <meshBasicMaterial color={ringColor} transparent opacity={0.7} />
      </mesh>
      <mesh position={[0, 0.18, 0]}>
        <sphereGeometry args={[0.12, 20, 20]} />
        <meshBasicMaterial color={ringColor} transparent opacity={0.9} />
      </mesh>
    </group>
  );
}

function ActuatorNode({ position, status, output, selected, onClick }) {
  const safePosition = normalizeEntityPosition(position);
  const active = output === 'active' || status === 'active';
  const color = active ? '#fbbf24' : '#64748b';
  return (
    <group position={safePosition} onClick={onClick} onPointerDown={onClick}>
      <mesh position={[0, 0.45, 0]} castShadow>
        <cylinderGeometry args={[0.38, 0.48, 0.9, 16]} />
        <meshStandardMaterial color={active ? '#f59e0b' : '#334155'} emissive={color} emissiveIntensity={active ? 0.55 : 0.12} metalness={0.55} roughness={0.3} />
      </mesh>
      <mesh position={[0, 0.95, 0]}>
        <sphereGeometry args={[0.12, 16, 16]} />
        <meshBasicMaterial color={color} />
      </mesh>
      {selected && <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.7, 0.07, 16, 64]} />
        <meshBasicMaterial color="#fef08a" transparent opacity={0.85} />
      </mesh>}
    </group>
  );
}

function IndustrialControlPanel({ robots, sensors, actuators, zones }) {
  const devices = [...robots, ...sensors, ...actuators];
  const unavailable = devices.filter((device) => ['offline', 'error', 'unknown'].includes(String(device.status || '').toLowerCase())).length;
  return (
    <div className="pointer-events-auto w-full rounded-2xl border border-cyan-400/25 bg-slate-950/80 p-3 text-[11px] font-mono text-cyan-100 shadow-[0_0_25px_rgba(34,211,238,0.12)] backdrop-blur-md">
      <div className="mb-2 flex items-center justify-between border-b border-cyan-500/20 pb-2">
        <span className="tracking-[0.28em] text-cyan-300 uppercase">Scene Inventory</span>
        <span className={`text-[10px] ${unavailable ? 'text-amber-300' : 'text-emerald-300'}`}>{unavailable ? `${unavailable} unavailable` : 'No reported faults'}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-slate-300">
        <span>Robots</span><span className="text-right">{robots.length}</span>
        <span>Sensors</span><span className="text-right">{sensors.length}</span>
        <span>Actuators</span><span className="text-right">{actuators.length}</span>
        <span>Zones</span><span className="text-right">{zones.length}</span>
      </div>
    </div>
  );
}

function SceneDynamics({ lightIntensity = 1, estateSpan = 100 }) {
  const sunPosition = [-estateSpan * 0.75, estateSpan * 1.6, estateSpan * 0.5];
  return (
    <>
      <directionalLight
        position={sunPosition}
        intensity={1.35 * lightIntensity}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        shadow-bias={-0.00015}
        shadow-normalBias={0.04}
        shadow-camera-near={1}
        shadow-camera-far={estateSpan * 4}
        shadow-camera-left={-estateSpan * 0.8}
        shadow-camera-right={estateSpan * 0.8}
        shadow-camera-top={estateSpan * 0.8}
        shadow-camera-bottom={-estateSpan * 0.8}
      />
      <directionalLight position={[estateSpan * 0.5, estateSpan * 0.3, -estateSpan * 0.5]} intensity={0.18 * lightIntensity} color="#c9d9e8" />
    </>
  );
}

// Main Estate Scene Component
export const EstateScene = ({ 
  robots = [], 
  sensors = [], 
  actuators = [],
  zones = [], 
  selectedEntity = null, 
  onEntitySelect = () => {},
  viewMode = 'realworld',
  lightIntensity = 1,
  autoRotate = false,
}) => {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return (
      <div className="h-full w-full bg-black/50 border border-aegis-primary/20 rounded-lg flex items-center justify-center">
        <div className="text-aegis-muted">Loading 3D Estate...</div>
      </div>
    );
  }

  const displayZones = normalizeDisplayEntities(zones, 'zone');
  const displayRobots = normalizeDisplayEntities(robots, 'robot');
  const displaySensors = normalizeDisplayEntities(sensors, 'sensor');
  const displayActuators = normalizeDisplayEntities(actuators, 'actuator');
  const attentionCount = displaySensors.filter((sensor) => ['warning', 'critical'].includes(String(sensor.state?.reading_status || '').toLowerCase())).length;
  const inferredCount = displayZones.filter((zone) => zone.spatial_status !== 'surveyed').length;
  const hasData = displayZones.length + displayRobots.length + displaySensors.length + displayActuators.length > 0;
  const zoneBounds = displayZones.map((zone) => {
    const position = normalizeEntityPosition(zone.position);
    const size = normalizeBuildingSize(zone.size);
    return {
      minX: position[0] - size[0] / 2,
      maxX: position[0] + size[0] / 2,
      minZ: position[2] - size[2] / 2,
      maxZ: position[2] + size[2] / 2,
    };
  });
  const minX = zoneBounds.length ? Math.min(...zoneBounds.map((bounds) => bounds.minX)) : -40;
  const maxX = zoneBounds.length ? Math.max(...zoneBounds.map((bounds) => bounds.maxX)) : 40;
  const minZ = zoneBounds.length ? Math.min(...zoneBounds.map((bounds) => bounds.minZ)) : -40;
  const maxZ = zoneBounds.length ? Math.max(...zoneBounds.map((bounds) => bounds.maxZ)) : 40;
  const centerX = (minX + maxX) / 2;
  const centerZ = (minZ + maxZ) / 2;
  const estateSpan = Math.max(maxX - minX, maxZ - minZ, 80);
  const cameraDistance = estateSpan * 1.15;
  const cameraPosition = viewMode === 'drone'
    ? [centerX + cameraDistance * 0.08, cameraDistance * 1.3, centerZ + cameraDistance * 0.14]
    : [centerX + cameraDistance, cameraDistance * 0.8, centerZ + cameraDistance];
  const groundSize = Math.max(estateSpan * 1.2, 160);

  return (
    <div className="flex h-full w-full flex-col gap-4">
      <div className="aegis-canvas-shell relative min-h-120 flex-1 overflow-hidden rounded-3xl border border-slate-800 bg-slate-950/95 shadow-[0_0_30px_rgba(34,211,238,0.14)]" style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.08), 0 0 35px rgba(34,211,238,0.12)' }}>
        <div className="pointer-events-none absolute left-4 top-4 z-10 rounded-full border border-cyan-500/30 bg-slate-950/65 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-200 shadow-[0_0_20px_rgba(34,211,238,0.1)] backdrop-blur-sm">
          LIVE TWIN
        </div>

        <div className="pointer-events-none absolute left-4 top-12 z-10 flex flex-wrap gap-2 font-mono text-[10px]">
          <span className={`rounded border px-2 py-1 ${attentionCount ? 'border-amber-500/40 bg-amber-950/70 text-amber-200' : 'border-emerald-500/30 bg-emerald-950/70 text-emerald-200'}`}>
            {attentionCount ? `${attentionCount} sensor conditions need attention` : 'Sensors within configured bands'}
          </span>
          <span className={`rounded border px-2 py-1 ${inferredCount ? 'border-slate-500/40 bg-slate-950/75 text-slate-300' : 'border-cyan-500/30 bg-slate-950/75 text-cyan-200'}`}>
            {inferredCount ? `${inferredCount} zone layouts inferred` : 'All zone layouts surveyed'}
          </span>
        </div>

        <div className="absolute bottom-4 right-4 z-10 font-mono text-[10px] text-aegis-muted pointer-events-none bg-black/60 border border-aegis-primary/30 p-3 rounded">
          <div className="space-y-1">
            <p>{displayRobots.length} robots</p>
            <p>{displaySensors.length} sensors</p>
            <p>{displayActuators.length} actuators</p>
            <p>{displayZones.length} zones</p>
          </div>
        </div>

        <Canvas
          style={{ width: '100%', height: '100%' }}
          camera={{ position: cameraPosition, fov: 55 }}
          shadows
          dpr={[1, 1.25]}
          gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
          onCreated={(state) => {
            state.gl.setPixelRatio(Math.min(window.devicePixelRatio, 1.25));
            state.gl.toneMapping = THREE.ACESFilmicToneMapping;
            state.gl.toneMappingExposure = 1.0;
            state.gl.outputColorSpace = THREE.SRGBColorSpace;
          }}
        >
          <color attach="background" args={[viewMode === 'wireframe' ? '#1a1a1a' : '#9fc4d7']} />
          <hemisphereLight skyColor="#dce9f4" groundColor="#526b5a" intensity={0.78 * lightIntensity} />
          <ambientLight intensity={0.35 * lightIntensity} />
          <SceneDynamics lightIntensity={lightIntensity} estateSpan={estateSpan} />

          <OrbitControls
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            enableDamping={true}
            autoRotate={autoRotate}
            autoRotateSpeed={1}
            dampingFactor={0.08}
            zoomSpeed={0.7}
            rotateSpeed={0.45}
            panSpeed={0.65}
            screenSpacePanning={true}
            target={[centerX, 0, centerZ]}
            maxDistance={estateSpan * 1.8}
            minDistance={6}
          />

            <fog attach="fog" args={[0x9fc4d7, estateSpan * 3, estateSpan * 7]} />

          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow>
            <planeGeometry args={[groundSize, groundSize]} />
            <meshStandardMaterial
                color={viewMode === 'wireframe' ? '#333333' : '#58744c'}
              roughness={0.95}
              metalness={0.05}
              wireframe={viewMode === 'wireframe'}
            />
          </mesh>
          {viewMode !== 'wireframe' && (
            <gridHelper
              args={[groundSize, Math.max(8, Math.ceil(groundSize / 20)), '#536d4d', '#70885b']}
              position={[0, 0.01, 0]}
            />
          )}

          {displayZones.map((zone) => {
            const safeZonePosition = normalizeEntityPosition(zone.position);
            return (
              <CoverageZone
                key={zone.id}
                zone={{ ...zone, position: safeZonePosition }}
                selected={selectedEntity?.type === 'zone' && selectedEntity.id === zone.id}
                onClick={() => onEntitySelect({ type: 'zone', id: zone.id, ...zone })}
              />
            );
          })}

          {displayZones.map((zone) => {
            const safeZonePosition = normalizeEntityPosition(zone.position);
            return (
              <Building
                key={`${zone.id}-building`}
                position={safeZonePosition}
                size={zone.size}
                color={zone.color}
                name={zone.name}
                spatialStatus={zone.spatial_status}
                lengthUnit={zone.length_unit}
                selected={selectedEntity?.type === 'zone' && selectedEntity.id === zone.id}
                onClick={() => onEntitySelect({ type: 'zone', id: zone.id, ...zone })}
              />
            );
          })}

          <ConnectionLines robots={displayRobots} sensors={displaySensors} />

          {displayRobots.map((robot) => {
            const safeRobotPosition = normalizeEntityPosition(robot.position);
            return (
              <group key={robot.id}>
                <DeviceStatusRing position={safeRobotPosition} status={robot.status} color="#34d399" selected={selectedEntity?.type === 'robot' && selectedEntity.id === robot.id} />
                <Robot
                  position={safeRobotPosition}
                  id={robot.id}
                  status={robot.status}
                  state={robot.state}
                  selected={selectedEntity?.type === 'robot' && selectedEntity.id === robot.id}
                  onClick={() => onEntitySelect({ type: 'robot', id: robot.id, ...robot })}
                />
              </group>
            );
          })}

          {displaySensors.map((sensor) => {
            const safeSensorPosition = normalizeEntityPosition(sensor.position);
            return (
              <group key={sensor.id}>
                <DeviceStatusRing position={safeSensorPosition} status={sensor.state?.reading_status || sensor.status || 'active'} color="#60a5fa" selected={selectedEntity?.type === 'sensor' && selectedEntity.id === sensor.id} />
                  <SensorNode
                    position={safeSensorPosition}
                    type={sensor.sensor_type || sensor.type || 'temperature'}
                    value={sensor.value}
                    unit={sensor.state?.unit}
                    readingStatus={sensor.state?.reading_status}
                    name={sensor.name}
                    selected={selectedEntity?.type === 'sensor' && selectedEntity.id === sensor.id}
                    onClick={() => onEntitySelect({ type: 'sensor', id: sensor.id, ...sensor })}
                  />
              </group>
            );
          })}

          {displayActuators.map((actuator) => {
            const safeActuatorPosition = normalizeEntityPosition(actuator.position);
            return (
              <group key={actuator.id}>
                <DeviceStatusRing position={safeActuatorPosition} status={actuator.state?.output === 'active' ? 'active' : actuator.status} color="#fbbf24" selected={selectedEntity?.type === 'actuator' && selectedEntity.id === actuator.id} />
                <ActuatorNode position={safeActuatorPosition} status={actuator.status} output={actuator.state?.output} selected={selectedEntity?.type === 'actuator' && selectedEntity.id === actuator.id} onClick={() => onEntitySelect({ type: 'actuator', id: actuator.id, ...actuator })} />
              </group>
            );
          })}
        </Canvas>

        {!hasData && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950/85">
            <div className="rounded-3xl border border-aegis-primary/30 bg-[#070b14]/95 p-6 text-center max-w-xs">
              <p className="text-sm text-aegis-muted">No estate data available.</p>
              <p className="mt-2 text-xs text-slate-400">Real robots, sensors and zones will appear here once data is loaded.</p>
            </div>
          </div>
        )}

        <div className="absolute inset-0 pointer-events-none opacity-5 bg-linear-to-b from-transparent via-aegis-primary to-transparent"></div>
        <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-aegis-primary/50"></div>
        <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-aegis-primary/50"></div>
        <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-aegis-primary/50"></div>
        <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-aegis-primary/50"></div>
      </div>

      <aside className="grid w-full grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1fr)_280px]">
        <IndustrialControlPanel robots={displayRobots} sensors={displaySensors} actuators={displayActuators} zones={displayZones} />
        <div className="rounded-2xl border border-cyan-500/25 bg-slate-950/80 p-3 text-[10px] font-mono uppercase tracking-[0.25em] text-cyan-200 shadow-[0_0_15px_rgba(34,211,238,0.08)] backdrop-blur-sm">
          <div className="space-y-2">
            <p>Robots: {displayRobots.length}</p>
            <p>Sensors: {displaySensors.length}</p>
            <p>Actuators: {displayActuators.length}</p>
            <p>Zones: {displayZones.length}</p>
          </div>
        </div>
      </aside>
    </div>
  );
};

export default EstateScene;
