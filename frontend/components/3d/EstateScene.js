import React, { useRef, useState, useEffect, Suspense, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Billboard, GizmoHelper, GizmoViewport, OrbitControls, Text, TransformControls, useGLTF } from '@react-three/drei';
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
const toDegrees = (radians) => radians * (180 / Math.PI);

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

function SceneTransform({ entity, selected, canTransform, transformMode, gridSnap, onCommit, children }) {
  const objectRef = useRef(null);
  const changedRef = useRef(false);
  const enabled = canTransform && selected && transformMode !== 'select'
    && (transformMode !== 'scale' || entity.type === 'zone');

  const commitTransform = () => {
    if (!changedRef.current || !objectRef.current) return;
    changedRef.current = false;
    const object = objectRef.current;
    onCommit?.(entity, {
      position: {
        x: object.position.x,
        y: object.position.y,
        z: object.position.z,
      },
      orientation: {
        x: toDegrees(object.rotation.x),
        y: toDegrees(object.rotation.y),
        z: toDegrees(object.rotation.z),
      },
      ...(entity.type === 'zone' && transformMode === 'scale' ? {
        dimensions: {
          width: (entity.size?.[0] || 1) * object.scale.x,
          height: (entity.size?.[1] || 1) * object.scale.y,
          depth: (entity.size?.[2] || 1) * object.scale.z,
        },
      } : {}),
    });
  };

  const object = (
    <group ref={objectRef} position={normalizeEntityPosition(entity.position)} rotation={normalizeEntityPosition(entity.rotation)}>
      {children}
    </group>
  );

  if (!enabled) return object;
  return (
    <TransformControls
      mode={transformMode}
      space="world"
      translationSnap={gridSnap}
      rotationSnap={transformMode === 'rotate' ? Math.PI / 12 : undefined}
      onObjectChange={() => { changedRef.current = true; }}
      onMouseUp={commitTransform}
    >
      {object}
    </TransformControls>
  );
}

// Building Structure Component
function Building({ position, size, color, name, spatialStatus, lengthUnit, selected, onClick, showLabels, showAllLabels }) {
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
      {showLabels && (showAllLabels || selected) && (
        <Billboard position={[0, wallHeight + 0.7, safeSize[2] / 2 + 1]}>
          <Text fontSize={selected ? 1.25 : 0.8} color="#f0fdf4" anchorX="center" anchorY="middle" textAlign="center" outlineWidth={0.06} outlineColor="#020617" depthOffset={-10}>
            {`${name || 'Estate zone'}\n${spatialStatus === 'surveyed' ? 'SURVEYED' : 'INFERRED'} · ${lengthUnit || 'm'}`}
          </Text>
        </Billboard>
      )}
    </group>
  );
}

// Robot Component
function Robot({ position, rotation = [0, 0, 0], status, state = {}, name, selected, onClick }) {
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
      groupRef.current.rotation.set(...rotation);
    }
    if (armRef.current) {
      armRef.current.rotation.z = moving ? Math.sin(robotTime.current * 3.2) * 0.18 : 0;
      armRef.current.rotation.x = moving ? Math.cos(robotTime.current * 1.8) * 0.1 : 0;
    }
  });

  const normalizedStatus = String(status || '').toLowerCase();
  const statusColor = ['offline', 'disconnected'].includes(normalizedStatus) ? '#64748b'
    : ['critical', 'error'].includes(normalizedStatus) ? '#ef4444'
      : normalizedStatus === 'warning' ? '#f59e0b'
        : normalizedStatus === 'charging' ? '#FF9500'
          : ['online', 'active', 'normal', 'idle', 'secure'].includes(normalizedStatus) ? '#34C759'
            : '#a78bfa';

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
      {selected && <Billboard position={[0, 1.15, 0]}><Text fontSize={0.3} color="#e2e8f0" anchorX="center" anchorY="bottom" outlineWidth={0.025} outlineColor="#020617">{name || 'Robot'}</Text></Billboard>}
    </group>
  );
}

// Sensor Node Component
function SensorNode({ position, rotation = [0, 0, 0], type, value, unit, readingStatus, name, selected, onClick, showLabels, showTelemetry }) {
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
    <group position={safePosition} rotation={rotation} onClick={onClick} onPointerDown={onClick}>
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
      {showLabels && selected && <Billboard position={[0, 0.95, 0]}><Text fontSize={0.3} color="#e2e8f0" anchorX="center" anchorY="bottom" outlineWidth={0.025} outlineColor="#020617">{name || type}</Text></Billboard>}
      {showTelemetry && value !== undefined && value !== null && (
        <Billboard position={[0, attention ? 1.58 : 1.28, 0]}>
          <Text fontSize={0.24} color="#bfdbfe" anchorX="center" anchorY="bottom" outlineWidth={0.025} outlineColor="#020617">
            {`${name || type}: ${value}${unit ? ` ${unit}` : ''}`}
          </Text>
        </Billboard>
      )}
    </group>
  );
}

function AssetConditionLabel({ status, lastUpdated, selected }) {
  const normalized = String(status || '').toLowerCase();
  const parsedTimestamp = lastUpdated ? new Date(lastUpdated).getTime() : NaN;
  const hasTimestamp = Number.isFinite(parsedTimestamp);
  const stale = hasTimestamp && Date.now() - parsedTimestamp >= 5 * 60 * 1000;
  const alertLabel = ['critical', 'warning', 'offline', 'error'].includes(normalized)
    ? normalized === 'error' ? 'OFFLINE' : normalized.toUpperCase()
    : null;
  const freshnessLabel = !hasTimestamp ? 'FRESHNESS UNKNOWN' : stale ? 'STALE' : null;
  const label = alertLabel || (selected ? freshnessLabel || (normalized === 'unknown' ? 'UNKNOWN' : null) : null);
  if (!label) return null;
  return (
    <Billboard position={[0, 1.65, 0]}>
      <Text fontSize={0.18} color={normalized === 'critical' || normalized === 'error' ? '#fecaca' : stale || normalized === 'warning' ? '#fde68a' : '#ddd6fe'} anchorX="center" anchorY="bottom" outlineWidth={0.02} outlineColor="#020617">
        {label}
      </Text>
    </Billboard>
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
    unknown: '#a78bfa',
    default: '#a5f3fc',
  };

  const ringColor = statusMap[String(status || '').toLowerCase()] || statusMap.unknown;

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

function ActuatorNode({ position, rotation = [0, 0, 0], status, output, name, selected, showLabels, onClick }) {
  const safePosition = normalizeEntityPosition(position);
  const active = output === 'active' || status === 'active';
  const color = active ? '#fbbf24' : '#64748b';
  return (
    <group position={safePosition} rotation={rotation} onClick={onClick} onPointerDown={onClick}>
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
      {showLabels && selected && <Billboard position={[0, 1.15, 0]}><Text fontSize={0.3} color="#e2e8f0" anchorX="center" anchorY="bottom" outlineWidth={0.025} outlineColor="#020617">{name || 'Actuator'}</Text></Billboard>}
    </group>
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
      <GizmoHelper alignment="bottom-left" margin={[72, 72]}>
        <GizmoViewport axisColors={['#ef4444', '#22c55e', '#3b82f6']} labelColor="#f8fafc" />
      </GizmoHelper>
      <directionalLight position={[estateSpan * 0.5, estateSpan * 0.3, -estateSpan * 0.5]} intensity={0.18 * lightIntensity} color="#c9d9e8" />
    </>
  );
}

function SceneCameraController({ preset, target, radius, focusTarget, focusRadius, zoomLevel, controlsRef, revision }) {
  const { camera, size } = useThree();
  const activeTarget = focusTarget || target;
  const targetX = activeTarget[0];
  const targetY = activeTarget[1];
  const targetZ = activeTarget[2];
  const activeRadius = focusTarget ? focusRadius : radius;

  useEffect(() => {
    const aspect = Math.max(size.width / Math.max(size.height, 1), 0.1);
    const verticalFov = THREE.MathUtils.degToRad(camera.fov);
    const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * aspect);
    const limitingFov = Math.min(verticalFov, horizontalFov);
    const distance = Math.max(activeRadius, 1) / Math.sin(limitingFov / 2) * 1.05 * zoomLevel;
    const positions = {
      home: [1, 0.78, 1],
      top: [0, 1, 0.001],
      front: [0, 0.3, 1],
      side: [1, 0.3, 0],
      isometric: [1, 0.62, 1],
    };
    const direction = new Vector3(...(positions[preset] || positions.home)).normalize();
    camera.position.set(targetX, targetY, targetZ).addScaledVector(direction, distance);
    camera.near = Math.max(0.01, distance / 1000);
    camera.far = Math.max(1000, distance * 12);
    camera.updateProjectionMatrix();
    camera.lookAt(targetX, targetY, targetZ);
    if (controlsRef.current) {
      controlsRef.current.target.set(targetX, targetY, targetZ);
      controlsRef.current.minDistance = Math.max(0.5, activeRadius * 0.025);
      controlsRef.current.maxDistance = Math.max(distance * 8, activeRadius * 8);
      controlsRef.current.update();
    }
  }, [activeRadius, camera, controlsRef, preset, size.height, size.width, targetX, targetY, targetZ, zoomLevel, revision]);

  return null;
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
  cameraPreset = 'home',
  interactionMode = 'orbit',
  transformMode = 'select',
  gridSnap = 1,
  canTransform = false,
  onTransformCommit = () => {},
  pendingTransforms = {},
  placementMode = false,
  placementKind = 'sensor',
  placementPosition = null,
  placementSize = [10, 4, 10],
  onViewportPlace = () => {},
  zoomLevel = 1,
  layers = {},
  labelDensity = 'selected',
  lightIntensity = 1,
  autoRotate = false,
  cameraRevision = 0,
  focusTarget = null,
  focusRadius = 4,
}) => {
  const [isClient, setIsClient] = useState(false);
  const controlsRef = useRef(null);

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

  const applyTransformDraft = (entity, fallbackType) => {
    const type = entity.type || fallbackType;
    const draft = pendingTransforms[`${type}:${entity.id}`];
    if (!draft) return { ...entity, type };
    const orientation = draft.orientation || entity.orientation;
    return {
      ...entity,
      type,
      position: draft.position || entity.position,
      orientation,
      rotation: orientation
        ? ['x', 'y', 'z'].map((axis) => (finiteNumber(orientation[axis], 0) * Math.PI) / 180)
        : entity.rotation,
      ...(draft.dimensions ? {
        dimensions: draft.dimensions,
        size: [draft.dimensions.width, draft.dimensions.height, draft.dimensions.depth],
      } : {}),
    };
  };
  const handleEntityClick = (event, entity) => {
    if (placementMode) {
      event.stopPropagation();
      return;
    }
    onEntitySelect(entity);
  };
  const displayZones = normalizeDisplayEntities(zones.map((zone) => applyTransformDraft(zone, 'zone')), 'zone');
  const displayRobots = normalizeDisplayEntities(robots.map((robot) => applyTransformDraft(robot, 'robot')), 'robot');
  const displaySensors = normalizeDisplayEntities(sensors.map((sensor) => applyTransformDraft(sensor, 'sensor')), 'sensor');
  const displayActuators = normalizeDisplayEntities(actuators.map((actuator) => applyTransformDraft(actuator, 'actuator')), 'actuator');
  const attentionCount = displaySensors.filter((sensor) => ['warning', 'critical'].includes(String(sensor.state?.reading_status || '').toLowerCase())).length;
  const inferredCount = displayZones.filter((zone) => zone.spatial_status !== 'surveyed').length;
  const hasData = displayZones.length + displayRobots.length + displaySensors.length + displayActuators.length > 0;
  const worldAssets = [...displayRobots, ...displaySensors, ...displayActuators];
  const hasSceneObjects = displayZones.length + worldAssets.length > 0;
  const bounds = {
    minX: hasSceneObjects ? Infinity : -40,
    maxX: hasSceneObjects ? -Infinity : 40,
    minY: 0,
    maxY: hasSceneObjects ? 0 : 6,
    minZ: hasSceneObjects ? Infinity : -40,
    maxZ: hasSceneObjects ? -Infinity : 40,
  };
  displayZones.forEach((zone) => {
    const position = normalizeEntityPosition(zone.position);
    const size = normalizeBuildingSize(zone.size);
    bounds.minX = Math.min(bounds.minX, position[0] - size[0] / 2);
    bounds.maxX = Math.max(bounds.maxX, position[0] + size[0] / 2);
    bounds.minY = Math.min(bounds.minY, position[1]);
    bounds.maxY = Math.max(bounds.maxY, position[1] + Math.min(Math.max(size[1], 3), 6) + 1.6);
    bounds.minZ = Math.min(bounds.minZ, position[2] - size[2] / 2);
    bounds.maxZ = Math.max(bounds.maxZ, position[2] + size[2] / 2);
  });
  worldAssets.forEach((asset) => {
    const position = normalizeEntityPosition(asset.position);
    bounds.minX = Math.min(bounds.minX, position[0] - 1.5);
    bounds.maxX = Math.max(bounds.maxX, position[0] + 1.5);
    bounds.minY = Math.min(bounds.minY, position[1]);
    bounds.maxY = Math.max(bounds.maxY, position[1] + 3);
    bounds.minZ = Math.min(bounds.minZ, position[2] - 1.5);
    bounds.maxZ = Math.max(bounds.maxZ, position[2] + 1.5);
  });
  const { minX, maxX, minY, maxY, minZ, maxZ } = bounds;
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const centerZ = (minZ + maxZ) / 2;
  const estateSpan = Math.max(maxX - minX, maxZ - minZ, 20);
  const sceneRadius = Math.max(Math.hypot((maxX - minX) / 2, (maxY - minY) / 2, (maxZ - minZ) / 2), 8);
  const cameraDistance = sceneRadius * 3 * zoomLevel;
  const cameraPosition = [centerX + cameraDistance, centerY + cameraDistance * 0.78, centerZ + cameraDistance];
  const groundSize = Math.max(estateSpan * 1.2, 160);
  const sceneLayers = {
    zones: layers.zones !== false,
    labels: layers.labels !== false,
    robots: layers.robots !== false,
    sensors: layers.sensors !== false,
    actuators: layers.actuators !== false,
    connections: layers.connections === true,
    grid: layers.grid !== false,
    alerts: layers.alerts !== false,
    telemetry: layers.telemetry === true,
  };
  const sceneTarget = [centerX, centerY, centerZ];

  return (
    <div className="flex h-full w-full flex-col gap-4">
      <div className="aegis-canvas-shell relative min-h-120 flex-1 overflow-hidden rounded-3xl border border-slate-800 bg-slate-950/95 shadow-[0_0_30px_rgba(34,211,238,0.14)]" style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.08), 0 0 35px rgba(34,211,238,0.12)' }}>
        <div className="pointer-events-none absolute left-4 top-4 z-10 rounded-full border border-cyan-500/30 bg-slate-950/65 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-200 shadow-[0_0_20px_rgba(34,211,238,0.1)] backdrop-blur-sm">
          3D DIGITAL TWIN
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
          fallback={<div role="status" className="flex h-full w-full items-center justify-center bg-slate-950 p-6 text-center text-sm text-amber-200">This device or browser does not support WebGL. Open the scene in a browser with hardware-accelerated graphics enabled.</div>}
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

          <SceneCameraController
            preset={cameraPreset}
            target={sceneTarget}
            radius={sceneRadius}
            focusTarget={focusTarget}
            focusRadius={focusRadius}
            zoomLevel={zoomLevel}
            revision={cameraRevision}
            controlsRef={controlsRef}
          />
          <OrbitControls
            ref={controlsRef}
            makeDefault
            enabled={!placementMode}
            enablePan={interactionMode === 'pan' || interactionMode === 'orbit'}
            enableZoom={true}
            enableRotate={interactionMode === 'orbit'}
            enableDamping={true}
            autoRotate={autoRotate}
            autoRotateSpeed={1}
            dampingFactor={0.08}
            zoomSpeed={0.7}
            rotateSpeed={0.45}
            panSpeed={0.65}
            screenSpacePanning={true}
            target={sceneTarget}
          />

          <fog attach="fog" args={[0x9fc4d7, estateSpan * 3, estateSpan * 7]} />

          <mesh
            rotation={[-Math.PI / 2, 0, 0]}
            position={[centerX, -0.02, centerZ]}
            receiveShadow
            onClick={(event) => {
              if (!placementMode) return;
              event.stopPropagation();
              onViewportPlace({ x: event.point.x, z: event.point.z });
            }}
          >
            <planeGeometry args={[groundSize, groundSize]} />
            <meshStandardMaterial
                color={viewMode === 'wireframe' ? '#333333' : '#58744c'}
              roughness={0.95}
              metalness={0.05}
              wireframe={viewMode === 'wireframe'}
            />
          </mesh>
          {sceneLayers.grid && viewMode !== 'wireframe' && (
            <gridHelper
              args={[groundSize, Math.max(8, Math.ceil(groundSize / 20)), '#536d4d', '#70885b']}
              position={[centerX, 0.01, centerZ]}
            />
          )}
          {placementPosition && (
            <mesh
              position={[placementPosition.x, placementPosition.y, placementPosition.z]}
              raycast={() => null}
            >
              <boxGeometry args={placementKind === 'zone' ? normalizeBuildingSize(placementSize) : [1.2, 1.2, 1.2]} />
              <meshBasicMaterial color="#22d3ee" wireframe transparent opacity={0.9} />
            </mesh>
          )}

          {sceneLayers.zones && displayZones.map((zone) => {
            const safeZonePosition = normalizeEntityPosition(zone.position);
            const selected = selectedEntity?.type === 'zone' && selectedEntity.id === zone.id;
            return (
              <SceneTransform
                key={zone.id}
                entity={{ ...zone, type: 'zone' }}
                selected={selected}
                canTransform={canTransform}
                transformMode={transformMode}
                gridSnap={gridSnap}
                onCommit={onTransformCommit}
              >
                <CoverageZone
                  zone={{ ...zone, position: [0, 0, 0] }}
                  selected={selected}
                  onClick={(event) => handleEntityClick(event, { type: 'zone', id: zone.id, ...zone })}
                />
                <Building
                  position={[0, 0, 0]}
                  size={zone.size}
                  color={zone.color}
                  name={zone.name}
                  spatialStatus={zone.spatial_status}
                  lengthUnit={zone.length_unit}
                  showLabels={sceneLayers.labels}
                  showAllLabels={labelDensity === 'all'}
                  selected={selected}
                  onClick={(event) => handleEntityClick(event, { type: 'zone', id: zone.id, ...zone })}
                />
              </SceneTransform>
            );
          })}

          {sceneLayers.connections && <ConnectionLines robots={displayRobots} sensors={displaySensors} />}

          {sceneLayers.robots && displayRobots.map((robot) => {
            return (
              <SceneTransform
                key={robot.id}
                entity={{ ...robot, type: 'robot' }}
                selected={selectedEntity?.type === 'robot' && selectedEntity.id === robot.id}
                canTransform={canTransform}
                transformMode={transformMode}
                gridSnap={gridSnap}
                onCommit={onTransformCommit}
              >
                {sceneLayers.alerts && <AssetConditionLabel status={robot.status} lastUpdated={robot.last_updated} selected={selectedEntity?.type === 'robot' && selectedEntity.id === robot.id} />}
                {sceneLayers.alerts && <DeviceStatusRing position={[0, 0, 0]} status={robot.status} color="#34d399" selected={selectedEntity?.type === 'robot' && selectedEntity.id === robot.id} />}
                <Robot
                  position={[0, 0, 0]}
                  id={robot.id}
                  status={robot.status}
                  state={robot.state}
                  name={robot.name}
                  selected={selectedEntity?.type === 'robot' && selectedEntity.id === robot.id}
                  onClick={(event) => handleEntityClick(event, { type: 'robot', id: robot.id, ...robot })}
                />
              </SceneTransform>
            );
          })}

          {sceneLayers.sensors && displaySensors.map((sensor) => {
            return (
              <SceneTransform
                key={sensor.id}
                entity={{ ...sensor, type: 'sensor' }}
                selected={selectedEntity?.type === 'sensor' && selectedEntity.id === sensor.id}
                canTransform={canTransform}
                transformMode={transformMode}
                gridSnap={gridSnap}
                onCommit={onTransformCommit}
              >
                {sceneLayers.alerts && <AssetConditionLabel status={sensor.state?.reading_status || sensor.status} lastUpdated={sensor.last_updated} selected={selectedEntity?.type === 'sensor' && selectedEntity.id === sensor.id} />}
                {sceneLayers.alerts && <DeviceStatusRing position={[0, 0, 0]} status={sensor.state?.reading_status || sensor.status || 'active'} color="#60a5fa" selected={selectedEntity?.type === 'sensor' && selectedEntity.id === sensor.id} />}
                  <SensorNode
                    position={[0, 0, 0]}
                    type={sensor.sensor_type || sensor.type || 'temperature'}
                    value={sensor.state?.value ?? sensor.value}
                    unit={sensor.state?.unit}
                    readingStatus={sensor.state?.reading_status}
                    name={sensor.name}
                    showLabels={sceneLayers.labels}
                    showTelemetry={sceneLayers.telemetry}
                    selected={selectedEntity?.type === 'sensor' && selectedEntity.id === sensor.id}
                    onClick={(event) => handleEntityClick(event, { type: 'sensor', id: sensor.id, ...sensor })}
                  />
              </SceneTransform>
            );
          })}

          {sceneLayers.actuators && displayActuators.map((actuator) => {
            return (
              <SceneTransform
                key={actuator.id}
                entity={{ ...actuator, type: 'actuator' }}
                selected={selectedEntity?.type === 'actuator' && selectedEntity.id === actuator.id}
                canTransform={canTransform}
                transformMode={transformMode}
                gridSnap={gridSnap}
                onCommit={onTransformCommit}
              >
                {sceneLayers.alerts && <AssetConditionLabel status={actuator.status} lastUpdated={actuator.last_updated} selected={selectedEntity?.type === 'actuator' && selectedEntity.id === actuator.id} />}
                {sceneLayers.alerts && <DeviceStatusRing position={[0, 0, 0]} status={actuator.state?.output === 'active' ? 'active' : actuator.status} color="#fbbf24" selected={selectedEntity?.type === 'actuator' && selectedEntity.id === actuator.id} />}
                <ActuatorNode position={[0, 0, 0]} rotation={actuator.rotation} status={actuator.status} output={actuator.state?.output} name={actuator.name} selected={selectedEntity?.type === 'actuator' && selectedEntity.id === actuator.id} showLabels={sceneLayers.labels} onClick={(event) => handleEntityClick(event, { type: 'actuator', id: actuator.id, ...actuator })} />
              </SceneTransform>
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

    </div>
  );
};

export default EstateScene;
