import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

// Building Structure Component
function Building({ position, size, color, name, selected, onClick }) {
  const [hovered, setHovered] = useState(false);
  const roofHeight = size[1] * 0.3;
  const baseHeight = size[1] - roofHeight;

  return (
    <group position={position}>
      {selected && (
        <mesh position={[0, baseHeight * 0.5 + 0.1, 0]} scale={[1.3, 1.3, 1.3]}> 
          <torusGeometry args={[Math.max(size[0], size[2]) * 0.7, 0.12, 16, 100]} />
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
        <boxGeometry args={[size[0], baseHeight, size[2]]} />
        <meshPhysicalMaterial
          color={selected ? '#8a2be2' : hovered ? '#2ee7ff' : color}
          roughness={0.22}
          metalness={0.2}
          clearcoat={0.15}
          clearcoatRoughness={0.1}
        />
      </mesh>

      <mesh position={[0, baseHeight / 2 + roofHeight / 2, 0]} castShadow>
        <coneGeometry args={[Math.max(size[0], size[2]) * 0.65, roofHeight, 4]} />
        <meshStandardMaterial
          color={selected ? '#ff66ff' : '#ffffff'}
          emissive={hovered ? '#6df2ff' : '#000000'}
          emissiveIntensity={hovered ? 0.25 : 0}
          metalness={0.1}
          roughness={0.4}
        />
      </mesh>

      <mesh position={[0, baseHeight * 0.2, size[2] / 2 + 0.01]}>
        <planeGeometry args={[size[0] * 0.8, baseHeight * 0.4]} />
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

  useFrame((state, delta) => {
    robotTime.current += delta;
    if (groupRef.current && isAnimating) {
      groupRef.current.position.y = position[1] + Math.sin(robotTime.current * 2) * 0.18;
    }
    if (armRef.current) {
      armRef.current.rotation.z = Math.sin(robotTime.current * 2) * 0.35;
    }
  });

  const statusColor = status === 'active' ? '#34C759' : status === 'charging' ? '#FF9500' : '#FF3B30';

  return (
    <group ref={groupRef} position={position} onClick={onClick}>
      {selected && (
        <mesh scale={[1.4, 1.4, 1.4]}> 
          <torusGeometry args={[0.55, 0.08, 16, 100]} />
          <meshBasicMaterial color="#ff66ff" transparent opacity={0.3} />
        </mesh>
      )}

      <mesh castShadow>
        <cylinderGeometry args={[0.35, 0.35, 0.45, 20]} />
        <meshPhysicalMaterial
          color={selected ? '#ff66ff' : '#0af0ff'}
          emissive={selected ? '#ff66ff' : statusColor}
          emissiveIntensity={selected ? 0.8 : 0.4}
          roughness={0.15}
          metalness={0.85}
        />
      </mesh>

      <mesh position={[0, 0.35, 0]} castShadow>
        <sphereGeometry args={[0.2, 32, 32]} />
        <meshPhysicalMaterial
          color={selected ? '#ff66ff' : '#15f0ff'}
          emissive={selected ? '#ff66ff' : statusColor}
          emissiveIntensity={selected ? 1.0 : 0.65}
          roughness={0.1}
          metalness={0.9}
        />
      </mesh>

      <group ref={armRef} position={[0.25, 0.05, 0]}> 
        <mesh castShadow>
          <boxGeometry args={[0.08, 0.3, 0.08]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.35} roughness={0.25} />
        </mesh>
        <mesh position={[0, 0.18, 0]} castShadow>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#ffea00" emissive="#facc15" emissiveIntensity={0.8} metalness={0.2} roughness={0.2} />
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

      <mesh position={[0.5, 0.15, 0]}>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshBasicMaterial color={statusColor} transparent opacity={0.95} />
      </mesh>
    </group>
  );
}

// Sensor Node Component
function SensorNode({ position, type, value, selected, onClick }) {
  const meshRef = useRef();
  const sensorTime = useRef(0);

  useFrame((state, delta) => {
    if (!meshRef.current) return;
    sensorTime.current += delta;
    const scale = selected ? 1.25 + Math.sin(sensorTime.current * 2) * 0.08 : 0.95 + Math.sin(sensorTime.current * 2) * 0.04;
    meshRef.current.scale.set(scale, scale, scale);
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
    <group position={position} onClick={onClick}>
      {selected && (
        <mesh scale={[1.4, 1.4, 1.4]}> 
          <torusGeometry args={[0.28, 0.06, 16, 100]} />
          <meshBasicMaterial color="#ff66ff" transparent opacity={0.2} />
        </mesh>
      )}
      <mesh ref={meshRef} castShadow>
        <icosahedronGeometry args={[0.22, 1]} />
        <meshPhysicalMaterial
          color={selected ? '#ff66ff' : color}
          emissive={selected ? '#ff66ff' : color}
          emissiveIntensity={selected ? 0.9 : 0.65}
          metalness={0.45}
          roughness={0.1}
        />
      </mesh>
      <mesh position={[0, -0.35, 0]}>
        <cylinderGeometry args={[0.04, 0.04, 0.2, 12]} />
        <meshStandardMaterial color="#0f172a" roughness={0.5} metalness={0.2} />
      </mesh>
    </group>
  );
}

// Connection Lines Component
function ConnectionLines({ robots, sensors }) {
  const getBeamTransform = (from, to) => {
    const start = new THREE.Vector3(...from);
    const end = new THREE.Vector3(...to);
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
          const distance = Math.hypot(
            robot.position[0] - sensor.position[0],
            robot.position[2] - sensor.position[2]
          );

          if (distance < 10) {
            const { midpoint, orientation, length } = getBeamTransform(robot.position, sensor.position);
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

// Main Estate Scene Component
export const EstateScene = ({ 
  robots = [], 
  sensors = [], 
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

  const displayZones = zones;
  const displayRobots = robots;
  const displaySensors = sensors;
  const hasData = displayZones.length || displayRobots.length || displaySensors.length;

  return (
    <div className="relative w-full h-full bg-slate-950/95 rounded-3xl overflow-hidden border border-slate-800 shadow-xl shadow-cyan-500/10">
      {/* Header Info */}
      <div className="absolute top-4 left-4 z-10 font-mono pointer-events-none">
        <h3 className="text-sm uppercase tracking-widest font-bold text-aegis-primary">
          🟢 ESTATE VISUALIZATION
        </h3>
        <p className="text-[11px] text-aegis-muted mt-1 uppercase tracking-tighter">
          {displayRobots.length} Robots • {displaySensors.length} Sensors • {displayZones.length} Zones
        </p>
      </div>

      {/* Stats */}
      <div className="absolute bottom-4 right-4 z-10 font-mono text-[10px] text-aegis-muted pointer-events-none bg-black/60 border border-aegis-primary/30 p-3 rounded">
        <div className="space-y-1">
          <p>FPS: 60</p>
          <p>Entities: {displayRobots.length + displaySensors.length + displayZones.length}</p>
          <p>Signal: NOMINAL</p>
        </div>
      </div>

      {/* Instructions */}
      <div className="absolute bottom-4 left-4 z-10 font-mono text-[10px] text-aegis-muted pointer-events-none">
        <p className="bg-black/60 border border-aegis-primary/30 px-2 py-1 rounded">
          🖱️ Drag to rotate • Scroll to zoom • Click to select
        </p>
      </div>

      {/* 3D Canvas */}
      <Canvas
        style={{ width: '100%', height: '100%' }}
        camera={{ position: viewMode === 'drone' ? [0, 25, 0] : [15, 12, 15], fov: 45 }}
        shadows
        shadowMap={{ type: THREE.PCFShadowMap }}
        gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
        onCreated={(state) => {
          state.gl.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        }}
      >
        <color attach="background" args={[viewMode === 'wireframe' ? 0x1a1a1a : 0x020916]} />
        {/* Lighting */}
        <ambientLight intensity={0.5 * lightIntensity} />
        <directionalLight
          position={[10, 15, 10]}
          intensity={1.5 * lightIntensity}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />
        <pointLight position={[-10, 10, -10]} intensity={0.8 * lightIntensity} color="#00ffff" />
        <pointLight position={[10, 5, 10]} intensity={0.6 * lightIntensity} color="#ff00ff" />

        {/* Controls */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          autoRotate={autoRotate}
          autoRotateSpeed={1}
          dampingFactor={0.05}
        />

        <fog attach="fog" args={[0x020916, 8, 50]} />

        {/* Ground */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow>
          <planeGeometry args={[60, 60]} />
          <meshStandardMaterial 
            color={viewMode === 'wireframe' ? '#333333' : '#07111d'} 
            roughness={0.95} 
            metalness={0.05}
            wireframe={viewMode === 'wireframe'}
          />
        </mesh>
        {viewMode !== 'wireframe' && (
          <gridHelper 
            args={[60, 60]} 
            position={[0, 0.01, 0]} 
          />
        )}

        {/* Zones/Buildings */}
        {displayZones.map((zone) => (
          <Building
            key={zone.id}
            position={zone.position}
            size={zone.size}
            color={zone.color}
            name={zone.name}
            selected={selectedEntity?.type === 'zone' && selectedEntity.id === zone.id}
            onClick={() => onEntitySelect({ type: 'zone', id: zone.id, ...zone })}
          />
        ))}

        {/* Connection Lines */}
        <ConnectionLines robots={displayRobots} sensors={displaySensors} />

        {/* Robots */}
        {displayRobots.map((robot) => (
          <Robot
            key={robot.id}
            position={robot.position}
            id={robot.id}
            status={robot.status}
            selected={selectedEntity?.type === 'robot' && selectedEntity.id === robot.id}
            onClick={() => onEntitySelect({ type: 'robot', id: robot.id, ...robot })}
            isAnimating={selectedEntity?.type === 'robot' && selectedEntity.id === robot.id}
          />
        ))}

        {/* Sensors */}
        {displaySensors.map((sensor) => (
          <SensorNode
            key={sensor.id}
            position={sensor.position}
            type={sensor.type}
            value={sensor.value}
            selected={selectedEntity?.type === 'sensor' && selectedEntity.id === sensor.id}
            onClick={() => onEntitySelect({ type: 'sensor', id: sensor.id, ...sensor })}
          />
        ))}
      </Canvas>
      {!hasData && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950/85">
          <div className="rounded-3xl border border-aegis-primary/30 bg-[#070b14]/95 p-6 text-center max-w-xs">
            <p className="text-sm text-aegis-muted">No estate data available.</p>
            <p className="mt-2 text-xs text-slate-400">Real robots, sensors and zones will appear here once data is loaded.</p>
          </div>
        </div>
      )}

      {/* Scanline Overlay */}
      <div className="absolute inset-0 pointer-events-none opacity-5 bg-gradient-to-b from-transparent via-aegis-primary to-transparent"></div>

      {/* Corner Markers */}
      <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-aegis-primary/50"></div>
      <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-aegis-primary/50"></div>
      <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-aegis-primary/50"></div>
      <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-aegis-primary/50"></div>
    </div>
  );
};

export default EstateScene;
