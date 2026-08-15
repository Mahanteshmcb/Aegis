import React, { Suspense, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Environment, Sky, ContactShadows, Html, useGLTF } from '@react-three/drei';
import { Box3, Vector3 } from 'three';

const FARMHOUSE_MODEL = '/models/CesiumMilkTruck.glb';
const FIELD_VEHICLE_MODEL = '/models/ToyCar.glb';
const FOREST_ASSET_MODEL = '/models/Fox.glb';
const HELMET_MODEL = '/models/DamagedHelmet.glb';
const PANEL_CRATE_MODEL = '/models/BoxTextured.glb';

useGLTF.preload(FARMHOUSE_MODEL);
useGLTF.preload(FIELD_VEHICLE_MODEL);
useGLTF.preload(FOREST_ASSET_MODEL);
useGLTF.preload(HELMET_MODEL);
useGLTF.preload(PANEL_CRATE_MODEL);

function normalizeScene(scene, targetHeight = 2) {
  const cloned = scene.clone(true);
  const box = new Box3().setFromObject(cloned);
  const size = box.getSize(new Vector3());
  const scaleFactor = targetHeight / Math.max(size.y, 1);
  cloned.scale.setScalar(scaleFactor);

  const scaledBox = new Box3().setFromObject(cloned);
  const center = scaledBox.getCenter(new Vector3());
  cloned.position.x -= center.x;
  cloned.position.z -= center.z;
  cloned.position.y -= scaledBox.min.y;

  return cloned;
}

function ModelAsset({ url, position = [0, 0, 0], rotation = [0, 0, 0], targetHeight = 2, scale = 1 }) {
  const { scene } = useGLTF(url);
  const assetScene = useMemo(() => {
    const normalized = normalizeScene(scene, targetHeight);
    normalized.scale.setScalar(normalized.scale.x * scale);
    return normalized;
  }, [scene, targetHeight, scale]);
  return <primitive object={assetScene} position={position} rotation={rotation} castShadow receiveShadow />;
}

function TwinSceneLoading() {
  return (
    <mesh position={[0, 1.2, 0]}>
      <sphereGeometry args={[1.4, 20, 20]} />
      <meshStandardMaterial color="#94a3b8" roughness={0.9} metalness={0.05} />
    </mesh>
  );
}

function SectionLabel({ name, position, color = '#ffffff' }) {
  return (
    <Html center position={position} style={{ pointerEvents: 'none', whiteSpace: 'nowrap' }}>
      <div className="rounded-xl border border-white/20 bg-slate-950/90 px-3 py-1 text-[10px] uppercase tracking-[0.3em] text-white shadow-lg shadow-black/20">
        {name}
      </div>
    </Html>
  );
}

function SolarArray({ position = [-12, 0.1, -12] }) {
  return (
    <group position={position}>
      {[...Array(6)].map((_, idx) => (
        <mesh key={idx} position={[idx * 1.8, 0, 0]} rotation={[-Math.PI / 2, 0, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.5, 0.05, 0.9]} />
          <meshStandardMaterial color="#0f172a" emissive="#38bdf8" emissiveIntensity={0.35} roughness={0.15} metalness={0.9} />
        </mesh>
      ))}
      <SectionLabel name="Solar Array" position={[5.2, 0.8, 0]} />
    </group>
  );
}

function WaterTower({ position = [10, 0, 10] }) {
  return (
    <group position={position}>
      <mesh position={[0, 1.2, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.5, 0.5, 2.4, 18]} />
        <meshStandardMaterial color="#64748b" roughness={0.35} metalness={0.6} />
      </mesh>
      <mesh position={[0, 2.45, 0]} castShadow>
        <cylinderGeometry args={[0.88, 0.88, 0.35, 24]} />
        <meshStandardMaterial color="#cbd5e1" roughness={0.25} metalness={0.35} />
      </mesh>
      <SectionLabel name="Water Tower" position={[0, 3.3, 0]} />
    </group>
  );
}

function DronePad({ position = [0, 0, 12] }) {
  return (
    <group position={position}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[3.5, 3.5, 0.1, 32]} />
        <meshStandardMaterial color="#0f172a" roughness={0.6} metalness={0.2} />
      </mesh>
      <mesh position={[0, 0.08, 0]}>
        <ringGeometry args={[1.2, 1.8, 32]} />
        <meshStandardMaterial color="#38bdf8" roughness={0.4} metalness={0.15} transparent opacity={0.85} />
      </mesh>
      <SectionLabel name="Drone Hub" position={[0, 0.75, 0]} />
    </group>
  );
}

function IrrigationPump({ position = [-8, 0, 10] }) {
  return (
    <group position={position}>
      <mesh castShadow>
        <boxGeometry args={[1.4, 0.55, 0.8]} />
        <meshStandardMaterial color="#111827" roughness={0.2} metalness={0.5} />
      </mesh>
      <mesh position={[0, 0.45, 0]}>
        <boxGeometry args={[1.28, 0.18, 0.68]} />
        <meshStandardMaterial color="#22c55e" emissive="#22c55e" emissiveIntensity={0.2} roughness={0.2} metalness={0.45} />
      </mesh>
      <SectionLabel name="Irrigation Relay" position={[0, 1.1, 0]} />
    </group>
  );
}

function Farmhouse({ position = [0, 0, 0] }) {
  return <ModelAsset url={FARMHOUSE_MODEL} position={position} rotation={[0, Math.PI / 4, 0]} targetHeight={4} scale={1.2} />;
}

function FieldVehicle({ position = [0, 0, 0], active = false }) {
  const ref = useRef();
  const offset = useMemo(() => Math.random() * Math.PI * 2, []);
  const localTime = useRef(0);

  useFrame((_, delta) => {
    if (ref.current) {
      localTime.current += delta;
      if (active) {
        const radius = 1.2;
        ref.current.position.x = position[0] + Math.sin(localTime.current * 0.6 + offset) * radius;
        ref.current.position.z = position[2] + Math.cos(localTime.current * 0.6 + offset) * radius;
      } else {
        ref.current.position.x = position[0];
        ref.current.position.z = position[2];
      }
      ref.current.rotation.y += delta * 0.35;
    }
  });

  return (
    <group ref={ref} position={position}>
      <ModelAsset url={FIELD_VEHICLE_MODEL} position={[0, 0, 0]} rotation={[0, Math.PI / 2, 0]} targetHeight={1.8} scale={0.9} />
    </group>
  );
}

function FoxAsset({ position = [12, 0, -2] }) {
  return <ModelAsset url={FOREST_ASSET_MODEL} position={position} rotation={[0, Math.PI * 1.1, 0]} targetHeight={2.2} />;
}

function HelmetSilo({ position = [8, 0, 6] }) {
  return <ModelAsset url={HELMET_MODEL} position={[position[0], 0, position[2]]} rotation={[0, Math.PI / 1.5, 0]} targetHeight={2.5} scale={1.1} />;
}

function AssetCrate({ position = [0, 0, 0], scale = [0.7, 0.7, 0.7], rotation = [0, 0, 0] }) {
  return <ModelAsset url={PANEL_CRATE_MODEL} position={position} rotation={rotation} targetHeight={1.8} scale={0.75} />;
}

function ZoneVolume({ zone, selected, hovered, onClick, onHover }) {
  const { width, height, depth } = useMemo(() => ({
    width: zone.size?.[0] || 8,
    height: Math.max(zone.size?.[1] || 2, 2),
    depth: zone.size?.[2] || 8,
  }), [zone.size]);
  const color = zone.color || '#16a34a';
  const active = selected || hovered;

  return (
    <group position={[zone.position?.[0] || 0, height / 2, zone.position?.[2] || 0]}>
      <mesh
        onClick={onClick}
        onPointerOver={onHover}
        onPointerOut={() => onHover(null)}
        castShadow
        receiveShadow
      >
        <boxGeometry args={[width, height, depth]} />
        <meshStandardMaterial
          transparent
          opacity={active ? 0.32 : 0.16}
          color={selected ? '#38bdf8' : hovered ? '#7dd3fc' : color}
          roughness={0.4}
          metalness={0.1}
        />
      </mesh>
      <SectionLabel name={zone.name || 'Zone'} position={[0, height + 0.45, 0]} />
    </group>
  );
}

function SensorPod({ sensor, selected, hovered, onClick, onHover }) {
  const colorMap = {
    temperature: '#ef4444',
    humidity: '#22c55e',
    motion: '#8b5cf6',
    pressure: '#38bdf8',
    light: '#facc15',
  };
  const color = colorMap[sensor.type] || '#34d399';
  const statusColor = selected ? '#60a5fa' : hovered ? '#93c5fd' : color;

  return (
    <group
      position={[sensor.position?.[0] || 0, 0.6, sensor.position?.[2] || 0]}
      onClick={onClick}
      onPointerOver={onHover}
      onPointerOut={() => onHover(null)}
    >
      <mesh castShadow>
        <cylinderGeometry args={[0.22, 0.22, 0.5, 18]} />
        <meshStandardMaterial color={statusColor} metalness={0.25} roughness={0.35} />
      </mesh>
      <mesh position={[0, 0.45, 0]}>
        <sphereGeometry args={[0.15, 16, 16]} />
        <meshStandardMaterial emissive={statusColor} emissiveIntensity={selected || hovered ? 1 : 0.5} color={statusColor} />
      </mesh>
      <SectionLabel name={sensor.name || sensor.type || 'Sensor'} position={[0, 1.2, 0]} />
    </group>
  );
}

function ControlSwitch({ switchData, selected, hovered, onClick, onHover }) {
  const baseColor = switchData.state === 'on' ? '#22c55e' : '#ef4444';
  const accent = selected ? '#38bdf8' : hovered ? '#60a5fa' : baseColor;

  return (
    <group
      position={[switchData.position?.[0] || 0, 0.4, switchData.position?.[2] || 0]}
      onClick={onClick}
      onPointerOver={onHover}
      onPointerOut={() => onHover(null)}
    >
      <mesh castShadow>
        <boxGeometry args={[0.6, 0.2, 0.4]} />
        <meshStandardMaterial color="#111827" metalness={0.6} roughness={0.2} />
      </mesh>
      <mesh position={[0, 0.15, 0]}>
        <boxGeometry args={[0.26, 0.06, 0.16]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={selected ? 0.9 : 0.6} />
      </mesh>
      <SectionLabel name={switchData.name || 'Panel'} position={[0, 0.95, 0]} />
    </group>
  );
}

function ControlVehicle({ robot, selected, hovered, onClick, onHover }) {
  const robotScale = selected || hovered ? 0.28 : 0.24;
  return (
    <group
      position={[robot.position?.[0] || 0, 0, robot.position?.[2] || 0]}
      onClick={onClick}
      onPointerOver={onHover}
      onPointerOut={() => onHover(null)}
    >
      <ModelAsset
        url={TOY_CAR_MODEL}
        position={[0, 0, 0]}
        rotation={[0, Math.PI, 0]}
        targetHeight={0.8}
        scale={robotScale}
      />
      {(selected || hovered) && (
        <mesh position={[0, 0.55, 0]}>
          <torusGeometry args={[0.45, 0.08, 16, 100]} />
          <meshBasicMaterial color={selected ? '#60a5fa' : '#93c5fd'} transparent opacity={0.25} />
        </mesh>
      )}
    </group>
  );
}

function GroundPlane() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[120, 120]} />
      <meshStandardMaterial color="#1f2937" roughness={0.95} metalness={0.05} />
    </mesh>
  );
}

export default function DigitalTwinScene({ robots = [], sensors = [], zones = [], switches = [], selectedEntity = null, onEntitySelect = () => {} }) {
  const defaultZones = useMemo(
    () => zones.length ? zones : [
      { id: 'zone-1', name: 'Crop Field A', position: [-10, 0, -8], size: [14, 1.5, 12], color: '#10b981', status: 'secure' },
      { id: 'zone-2', name: 'Livestock Zone', position: [10, 0, -8], size: [12, 1.5, 12], color: '#f97316', status: 'warning' },
      { id: 'zone-3', name: 'Drone Pad', position: [0, 0, 12], size: [10, 1.5, 10], color: '#38bdf8', status: 'secure' },
    ], [zones]
  );

  const defaultSensors = useMemo(
    () => sensors.length ? sensors : [
      { id: 'sensor-1', type: 'temperature', name: 'Thermal Node', position: [-6, 0, -4], status: 'active' },
      { id: 'sensor-2', type: 'humidity', name: 'Moisture Node', position: [6, 0, -4], status: 'active' },
      { id: 'sensor-3', type: 'motion', name: 'Security Beacon', position: [0, 0, 8], status: 'idle' },
    ], [sensors]
  );

  const defaultSwitches = useMemo(
    () => switches.length ? switches : [
      { id: 'switch-1', name: 'Irrigation Relay', state: 'on', position: [-10, 0, 10] },
      { id: 'switch-2', name: 'Power Gate', state: 'off', position: [10, 0, 10] },
    ], [switches]
  );

  const defaultRobots = useMemo(
    () => robots.length ? robots : [
      { id: 'robot-1', name: 'Field Rover A', position: [-8, 0, 4], status: 'active' },
      { id: 'robot-2', name: 'Inspection Bot', position: [8, 0, 4], status: 'charging' },
    ], [robots]
  );

  const [hoveredEntity, setHoveredEntity] = useState(null);
  const handleHover = (entity) => setHoveredEntity(entity);

  return (
    <div className="relative w-full h-full overflow-hidden rounded-3xl border border-slate-800 shadow-xl shadow-cyan-500/10 bg-slate-950">
      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [25, 18, 26], fov: 45 }}
        gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
      >
        <color attach="background" args={[0.06, 0.10, 0.14]} />
        <Sky sunPosition={[10, 20, 10]} turbidity={6} rayleigh={0.45} />
        <Environment preset="forest" />
        <ambientLight intensity={0.45} />
        <directionalLight
          castShadow
          position={[18, 25, 18]}
          intensity={1.2}
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
          shadow-camera-left={-30}
          shadow-camera-right={30}
          shadow-camera-top={30}
          shadow-camera-bottom={-30}
        />

        <pointLight position={[-20, 12, -12]} intensity={0.4} color="#a5b4fc" />
        <pointLight position={[8, 8, -16]} intensity={0.3} color="#fcd34d" />

        <GroundPlane />

        <Suspense fallback={<TwinSceneLoading />}>
          <Farmhouse position={[0, 0, -2]} />
          <FoxAsset position={[10, 0, 0]} />
          <HelmetSilo position={[12, 0, 6]} />
          <SectionLabel name="Estate Control" position={[0, 5.8, -2]} />
          <SolarArray />
          <WaterTower />
          <DronePad />
          <IrrigationPump />
          <AssetCrate position={[-14, 0, -8]} rotation={[0, Math.PI / 2, 0]} />
          <AssetCrate position={[14, 0, -8]} rotation={[0, Math.PI / 1.7, 0]} />

          {defaultZones.map((zone) => (
          <ZoneVolume
            key={zone.id}
            zone={zone}
            selected={selectedEntity?.id === zone.id && selectedEntity?.type === 'zone'}
            hovered={hoveredEntity?.id === zone.id && hoveredEntity?.type === 'zone'}
            onClick={() => onEntitySelect({ ...zone, type: 'zone' })}
            onHover={() => handleHover({ ...zone, type: 'zone' })}
          />
        ))}

        {defaultSensors.map((sensor) => (
          <SensorPod
            key={sensor.id}
            sensor={sensor}
            selected={selectedEntity?.id === sensor.id && selectedEntity?.type === 'sensor'}
            hovered={hoveredEntity?.id === sensor.id && hoveredEntity?.type === 'sensor'}
            onClick={() => onEntitySelect({ ...sensor, type: 'sensor' })}
            onHover={() => handleHover({ ...sensor, type: 'sensor' })}
          />
        ))}

        {defaultSwitches.map((sw) => (
          <ControlSwitch
            key={sw.id}
            switchData={sw}
            selected={selectedEntity?.id === sw.id && selectedEntity?.type === 'switch'}
            hovered={hoveredEntity?.id === sw.id && hoveredEntity?.type === 'switch'}
            onClick={() => onEntitySelect({ ...sw, type: 'switch' })}
            onHover={() => handleHover({ ...sw, type: 'switch' })}
          />
        ))}

        {defaultRobots.map((robot) => (
          <group key={robot.id}>
            <ControlVehicle
              robot={robot}
              selected={selectedEntity?.id === robot.id && selectedEntity?.type === 'robot'}
              hovered={hoveredEntity?.id === robot.id && hoveredEntity?.type === 'robot'}
              onClick={() => onEntitySelect({ ...robot, type: 'robot' })}
              onHover={() => handleHover({ ...robot, type: 'robot' })}
            />
            <FieldVehicle position={[robot.position[0], 0, robot.position[2] + 2]} active={robot.status === 'active'} />
          </group>
        ))}
        </Suspense>

        <ContactShadows position={[0, -0.1, 0]} opacity={0.7} scale={80} blur={2.5} far={20} />
        <OrbitControls enablePan enableZoom enableRotate screenSpacePanning={false} maxDistance={70} minDistance={10} />
      </Canvas>

      <TwinStatusHud
        selectedEntity={selectedEntity}
        hoveredEntity={hoveredEntity}
        robots={defaultRobots}
        sensors={defaultSensors}
        zones={defaultZones}
        switches={defaultSwitches}
      />

      <div className="absolute top-4 left-4 z-20 rounded-2xl border border-white/10 bg-black/70 p-4 text-xs text-slate-200 shadow-xl shadow-slate-950/30 backdrop-blur">
        <div className="font-semibold text-white mb-2">Digital Twin</div>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-xl bg-slate-900/80 p-2">
            <p className="text-[10px] uppercase tracking-[0.3em] text-slate-400">Zones</p>
            <p className="text-sm font-semibold text-white">{defaultZones.length}</p>
          </div>
          <div className="rounded-xl bg-slate-900/80 p-2">
            <p className="text-[10px] uppercase tracking-[0.3em] text-slate-400">Sensors</p>
            <p className="text-sm font-semibold text-white">{defaultSensors.length}</p>
          </div>
          <div className="rounded-xl bg-slate-900/80 p-2">
            <p className="text-[10px] uppercase tracking-[0.3em] text-slate-400">Robots</p>
            <p className="text-sm font-semibold text-white">{defaultRobots.length}</p>
          </div>
          <div className="rounded-xl bg-slate-900/80 p-2">
            <p className="text-[10px] uppercase tracking-[0.3em] text-slate-400">Switches</p>
            <p className="text-sm font-semibold text-white">{defaultSwitches.length}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function TwinStatusHud({ selectedEntity, hoveredEntity, robots, sensors, zones, switches }) {
  const activeEntity = selectedEntity || hoveredEntity;
  return (
    <div className="absolute bottom-4 right-4 z-20 w-72 rounded-3xl border border-white/10 bg-slate-950/90 p-4 text-xs text-slate-200 shadow-2xl shadow-slate-950/40 backdrop-blur">
      <div className="mb-3 text-[10px] uppercase tracking-[0.35em] text-slate-400">Estate Digital Twin</div>
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="rounded-2xl bg-slate-900/80 p-3">
          <div className="text-[10px] uppercase tracking-[0.3em] text-slate-400">Robots</div>
          <div className="mt-1 text-lg font-bold text-cyan-300">{robots.length}</div>
        </div>
        <div className="rounded-2xl bg-slate-900/80 p-3">
          <div className="text-[10px] uppercase tracking-[0.3em] text-slate-400">Sensors</div>
          <div className="mt-1 text-lg font-bold text-emerald-300">{sensors.length}</div>
        </div>
        <div className="rounded-2xl bg-slate-900/80 p-3">
          <div className="text-[10px] uppercase tracking-[0.3em] text-slate-400">Zones</div>
          <div className="mt-1 text-lg font-bold text-violet-300">{zones.length}</div>
        </div>
        <div className="rounded-2xl bg-slate-900/80 p-3">
          <div className="text-[10px] uppercase tracking-[0.3em] text-slate-400">Switches</div>
          <div className="mt-1 text-lg font-bold text-amber-300">{switches.length}</div>
        </div>
      </div>
      <div className="rounded-2xl bg-slate-900/80 p-3 border border-white/10">
        <div className="text-[10px] uppercase tracking-[0.3em] text-slate-400">Current Focus</div>
        {activeEntity ? (
          <div className="mt-2 text-sm font-semibold text-white">{activeEntity.name || activeEntity.type}</div>
        ) : (
          <div className="mt-2 text-sm text-slate-300">Hover or select a zone, sensor, robot, or switch</div>
        )}
      </div>
    </div>
  );
}

function Label({ name, position }) {
  return <SectionLabel name={name} position={position} />;
}
