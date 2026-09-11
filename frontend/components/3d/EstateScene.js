import React, { useRef, useState, useEffect, Suspense, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sky, useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { Box3, Vector3 } from 'three';
import EstateEnvironmentAssets from './EstateEnvironmentAssets';
import EstateMasterLayout from './EstateMasterLayout';

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
function Building({ position, size, color, name, selected, onClick }) {
  const [hovered, setHovered] = useState(false);
  const safePosition = normalizeEntityPosition(position);
  const safeSize = normalizeBuildingSize(size);
  const roofHeight = safeSize[1] * 0.3;
  const baseHeight = Math.max(safeSize[1] - roofHeight, 0.1);

  return (
    <group position={safePosition}>
      {selected && (
        <mesh position={[0, baseHeight * 0.5 + 0.1, 0]} scale={[1.3, 1.3, 1.3]}>
          <torusGeometry args={[Math.max(safeSize[0], safeSize[2]) * 0.7, 0.12, 16, 100]} />
          <meshBasicMaterial color="#ff66ff" transparent opacity={0.35} />
        </mesh>
      )}

      <mesh
        onClick={onClick}
        onPointerEnter={() => setHovered(true)}
        onPointerLeave={() => setHovered(false)}
        castShadow
        receiveShadow
      >
        <boxGeometry args={[safeSize[0], baseHeight, safeSize[2]]} />
        <meshPhysicalMaterial
          color={selected ? '#8a2be2' : hovered ? '#2ee7ff' : color}
          roughness={0.22}
          metalness={0.2}
          clearcoat={0.15}
          clearcoatRoughness={0.1}
        />
      </mesh>

      <mesh position={[0, baseHeight / 2 + roofHeight / 2, 0]} castShadow>
        <coneGeometry args={[Math.max(safeSize[0], safeSize[2]) * 0.65, roofHeight, 4]} />
        <meshStandardMaterial
          color={selected ? '#ff66ff' : '#ffffff'}
          emissive={hovered ? '#6df2ff' : '#000000'}
          emissiveIntensity={hovered ? 0.25 : 0}
          metalness={0.1}
          roughness={0.4}
        />
      </mesh>

      <mesh position={[0, baseHeight * 0.2, safeSize[2] / 2 + 0.01]}>
        <planeGeometry args={[safeSize[0] * 0.8, baseHeight * 0.4]} />
        <meshStandardMaterial color="#1f2937" emissive="#0f172a" emissiveIntensity={0.05} />
      </mesh>
    </group>
  );
}

// Robot Component
function Robot({ position, id, status, selected, onClick, isAnimating }) {
  const groupRef = useRef();
  const armRef = useRef();
  const robotTime = useRef(0);
  const hoverOffset = useRef(Math.random() * Math.PI * 2);
  const safePosition = normalizeEntityPosition(position);
  const basePosition = useRef(new THREE.Vector3(...safePosition));

  useFrame((state, delta) => {
    robotTime.current += delta;
    if (groupRef.current) {
      const floatY = Math.sin(robotTime.current * 2.1 + hoverOffset.current) * 0.18;
      const driftX = Math.sin(robotTime.current * 1.4 + hoverOffset.current) * 0.2;
      groupRef.current.position.set(
        basePosition.current.x + driftX,
        safePosition[1] + floatY,
        basePosition.current.z + Math.cos(robotTime.current * 1.8 + hoverOffset.current) * 0.2,
      );
      groupRef.current.rotation.y = Math.sin(robotTime.current * 0.9 + hoverOffset.current) * 0.5;
      groupRef.current.rotation.z = Math.sin(robotTime.current * 1.6 + hoverOffset.current) * 0.08;
    }
    if (armRef.current) {
      armRef.current.rotation.z = Math.sin(robotTime.current * 3.2 + hoverOffset.current) * 0.45;
      armRef.current.rotation.x = Math.cos(robotTime.current * 1.8 + hoverOffset.current) * 0.22;
    }
  });

  const statusColor = status === 'active' ? '#34C759' : status === 'charging' ? '#FF9500' : '#FF3B30';

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
function SensorNode({ position, type, value, selected, onClick }) {
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
  const radius = Math.max(safeSize[0], safeSize[2]) * 0.48;
  const color = zone.color || '#38bdf8';

  return (
    <group position={safePosition} onClick={onClick}>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[radius * 0.9, radius, 64]} />
        <meshBasicMaterial color={color} transparent opacity={selected ? 0.8 : 0.45} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0, safeSize[1] * 0.15, 0]}>
        <cylinderGeometry args={[radius * 0.82, radius * 0.82, Math.max(safeSize[1], 1.2), 32, 1, true]} />
        <meshBasicMaterial color={color} transparent opacity={selected ? 0.28 : 0.16} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0, 0.15, 0]}>
        <cylinderGeometry args={[radius * 0.88, radius * 0.88, 0.12, 32]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.28} metalness={0.3} roughness={0.4} />
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

function IndustrialControlPanel({ onCommand }) {
  const commandButtons = [
    { label: 'Start patrol', action: 'patrol' },
    { label: 'Inspect zone', action: 'inspection' },
    { label: 'Camera verify', action: 'camera' },
    { label: 'Lock gate', action: 'gate' },
  ];

  return (
    <div className="pointer-events-auto w-full rounded-2xl border border-cyan-400/25 bg-slate-950/80 p-3 text-[11px] font-mono text-cyan-100 shadow-[0_0_25px_rgba(34,211,238,0.12)] backdrop-blur-md">
      <div className="mb-2 flex items-center justify-between border-b border-cyan-500/20 pb-2">
        <span className="tracking-[0.28em] text-cyan-300 uppercase">Control</span>
        <span className="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-1.5 py-0.5 text-[10px] text-emerald-300">Live</span>
      </div>
      <div className="mb-3 grid grid-cols-2 gap-2">
        <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-2">
          <div className="text-slate-400">System</div>
          <div className="mt-1 text-[13px] font-semibold text-emerald-300">Nominal</div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-2">
          <div className="text-slate-400">Network</div>
          <div className="mt-1 text-[13px] font-semibold text-cyan-300">98.4%</div>
        </div>
      </div>
      <div className="space-y-2">
        {commandButtons.map((button) => (
          <button
            key={button.action}
            onClick={() => onCommand?.(button.action)}
            className="w-full rounded-lg border border-cyan-500/25 bg-cyan-500/5 px-2 py-2 text-left text-cyan-100 transition hover:border-cyan-300/60 hover:bg-cyan-500/10"
          >
            {button.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function SceneDynamics({ lightIntensity = 1 }) {
  const sunRef = useRef();
  const glowRef = useRef();
  const hazeRef = useRef();
  const rimRef = useRef();

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (sunRef.current) {
      sunRef.current.position.set(18, 30, 16);
      sunRef.current.intensity = 2.2 * lightIntensity;
    }
    if (glowRef.current) {
      glowRef.current.material.opacity = 0.08 + Math.sin(t * 0.7) * 0.02;
    }
    if (hazeRef.current) {
      hazeRef.current.rotation.y = t * 0.04;
      hazeRef.current.position.y = 12 + Math.sin(t * 0.3) * 0.7;
    }
    if (rimRef.current) {
      rimRef.current.intensity = 1.35 * lightIntensity;
    }
  });

  return (
    <>
      <mesh ref={glowRef} position={[0, 18, 0]} scale={[1.2, 1.2, 1.2]}>
        <sphereGeometry args={[28, 28, 28]} />
        <meshBasicMaterial color="#7dd3fc" transparent opacity={0.08} side={THREE.BackSide} />
      </mesh>
      <mesh ref={hazeRef} position={[0, 12, 0]} rotation={[0, 0, 0]}>
        <sphereGeometry args={[32, 24, 24]} />
        <meshBasicMaterial color="#dfeeff" transparent opacity={0.04} side={THREE.BackSide} />
      </mesh>
      <directionalLight
        ref={sunRef}
        position={[18, 30, 16]}
        intensity={2.2 * lightIntensity}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        shadow-bias={-0.00015}
        shadow-normalBias={0.04}
        shadow-camera-near={1}
        shadow-camera-far={120}
        shadow-camera-left={-70}
        shadow-camera-right={70}
        shadow-camera-top={70}
        shadow-camera-bottom={-70}
      />
      <pointLight ref={rimRef} position={[-12, 12, -12]} intensity={1.35 * lightIntensity} color="#67e8f9" />
      <pointLight position={[-10, 10, -10]} intensity={0.75 * lightIntensity} color="#b9efff" />
      <pointLight position={[10, 8, 10]} intensity={0.65 * lightIntensity} color="#b7d7ff" />
      <pointLight position={[8, 5, -10]} intensity={0.35 * lightIntensity} color="#ffd0ef" />
      <spotLight position={[0, 24, 0]} angle={0.38} penumbra={0.8} intensity={1.1 * lightIntensity} color="#fff4dc" />
    </>
  );
}

// Main Estate Scene Component
export const EstateScene = ({ 
  robots = [], 
  sensors = [], 
  zones = [], 
  selectedEntity = null, 
  onEntitySelect = () => {},
  onCommand = () => {},
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

  const displayZones = zones;
  const displayRobots = robots;
  const displaySensors = sensors;
  const hasData = displayZones.length || displayRobots.length || displaySensors.length;

  return (
    <div className="flex h-full w-full flex-col gap-4">
      <div className="aegis-canvas-shell relative min-h-[480px] flex-1 overflow-hidden rounded-3xl border border-slate-800 bg-slate-950/95 shadow-[0_0_30px_rgba(34,211,238,0.14)]" style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.08), 0 0 35px rgba(34,211,238,0.12)' }}>
        <div className="pointer-events-none absolute left-4 top-4 z-10 rounded-full border border-cyan-500/30 bg-slate-950/65 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-200 shadow-[0_0_20px_rgba(34,211,238,0.1)] backdrop-blur-sm">
          LIVE TWIN
        </div>

        <div className="absolute bottom-4 right-4 z-10 font-mono text-[10px] text-aegis-muted pointer-events-none bg-black/60 border border-aegis-primary/30 p-3 rounded">
          <div className="space-y-1">
            <p>{displayRobots.length} robots</p>
            <p>{displaySensors.length} sensors</p>
            <p>{displayZones.length} zones</p>
          </div>
        </div>

        <Canvas
          style={{ width: '100%', height: '100%' }}
          camera={{ position: viewMode === 'drone' ? [0, 95, 0] : [78, 64, 86], fov: 52 }}
          shadows
          dpr={[1, 1.25]}
          gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
          onCreated={(state) => {
            state.gl.setPixelRatio(Math.min(window.devicePixelRatio, 1.25));
            state.gl.toneMapping = THREE.ACESFilmicToneMapping;
            state.gl.toneMappingExposure = 1.2;
            state.gl.outputColorSpace = THREE.SRGBColorSpace;
          }}
        >
          <color attach="background" args={[viewMode === 'wireframe' ? 0x1a1a1a : 0x020916]} />
          <Sky sunPosition={[-30, 45, 20]} turbidity={2.2} rayleigh={0.35} />
          <hemisphereLight skyColor="#fff4dc" groundColor="#526b5a" intensity={0.95 * lightIntensity} />
          <ambientLight intensity={0.72 * lightIntensity} />
          <SceneDynamics lightIntensity={lightIntensity} />

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
            maxDistance={140}
            minDistance={6}
          />

          <fog attach="fog" args={[0x17241c, 45, 220]} />

          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow>
            <planeGeometry args={[240, 240]} />
            <meshStandardMaterial
              color={viewMode === 'wireframe' ? '#333333' : '#07111d'}
              roughness={0.95}
              metalness={0.05}
              wireframe={viewMode === 'wireframe'}
            />
          </mesh>
          {viewMode !== 'wireframe' && (
            <gridHelper
              args={[160, 40, '#496658', '#263a31']}
              position={[0, 0.01, 0]}
            />
          )}

          {viewMode !== 'wireframe' && <EstateMasterLayout />}

          {viewMode !== 'wireframe' && <EstateEnvironmentAssets />}

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
                  selected={selectedEntity?.type === 'robot' && selectedEntity.id === robot.id}
                  onClick={() => onEntitySelect({ type: 'robot', id: robot.id, ...robot })}
                  isAnimating={selectedEntity?.type === 'robot' && selectedEntity.id === robot.id}
                />
              </group>
            );
          })}

          {displaySensors.map((sensor) => {
            const safeSensorPosition = normalizeEntityPosition(sensor.position);
            return (
              <group key={sensor.id}>
                <DeviceStatusRing position={safeSensorPosition} status={sensor.status || 'active'} color="#60a5fa" selected={selectedEntity?.type === 'sensor' && selectedEntity.id === sensor.id} />
                  <SensorNode
                    position={safeSensorPosition}
                    type={sensor.sensor_type || sensor.type || 'temperature'}
                    value={sensor.value}
                    selected={selectedEntity?.type === 'sensor' && selectedEntity.id === sensor.id}
                    onClick={() => onEntitySelect({ type: 'sensor', id: sensor.id, ...sensor })}
                  />
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

        <div className="absolute inset-0 pointer-events-none opacity-5 bg-gradient-to-b from-transparent via-aegis-primary to-transparent"></div>
        <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-aegis-primary/50"></div>
        <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-aegis-primary/50"></div>
        <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-aegis-primary/50"></div>
        <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-aegis-primary/50"></div>
      </div>

      <aside className="grid w-full grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1fr)_280px]">
        <IndustrialControlPanel onCommand={onCommand} />
        <div className="rounded-2xl border border-cyan-500/25 bg-slate-950/80 p-3 text-[10px] font-mono uppercase tracking-[0.25em] text-cyan-200 shadow-[0_0_15px_rgba(34,211,238,0.08)] backdrop-blur-sm">
          <div className="space-y-2">
            <p>Robots: {displayRobots.length}</p>
            <p>Sensors: {displaySensors.length}</p>
            <p>Zones: {displayZones.length}</p>
          </div>
        </div>
      </aside>
    </div>
  );
};

export default EstateScene;
