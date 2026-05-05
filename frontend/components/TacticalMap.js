import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Grid, PerspectiveCamera, Float, Stars } from '@react-three/drei';
import * as THREE from 'three';

function RotatingCore({ anomaly }) {
  const meshRef = useRef();
  const orbitRef = useRef();
  
  useFrame((state, delta) => {
    if (meshRef.current) {
      const speed = anomaly ? 3.0 : 0.5;
      meshRef.current.rotation.y += delta * speed;
      meshRef.current.rotation.z += delta * (speed / 2);
    }
    
    // Orbit satellite around core
    if (orbitRef.current) {
      orbitRef.current.rotation.z += delta * (anomaly ? 2 : 0.3);
    }
  });

  return (
    <>
      {/* Central Core */}
      <Float speed={anomaly ? 5 : 1.5} rotationIntensity={2} floatIntensity={2}>
        <mesh ref={meshRef}>
          <octahedronGeometry args={[1, 2]} />
          <meshStandardMaterial 
            color={anomaly ? "#ff0044" : "#00f2ff"} 
            wireframe={false}
            emissive={anomaly ? "#ff0044" : "#00f2ff"} 
            emissiveIntensity={anomaly ? 10 : 3}
            metalness={0.8}
            roughness={0.2}
          />
        </mesh>
        <mesh>
          <octahedronGeometry args={[1.3, 1]} />
          <meshBasicMaterial 
            color={anomaly ? "#ff0044" : "#00f2ff"} 
            wireframe 
            transparent 
            opacity={0.4}
          />
        </mesh>
      </Float>

      {/* Orbiting Satellites */}
      <group ref={orbitRef}>
        {[0, 120, 240].map((offset) => (
          <group key={offset} rotation={[0, (offset * Math.PI) / 180, 0]}>
            <mesh position={[3, 0, 0]}>
              <sphereGeometry args={[0.2, 8, 8]} />
              <meshStandardMaterial 
                color={anomaly ? "#ff6600" : "#00ff88"} 
                emissive={anomaly ? "#ff6600" : "#00ff88"}
                emissiveIntensity={5}
              />
            </mesh>
            {/* Connecting lines */}
            <line position={[0, 0, 0]}>
              <bufferGeometry>
                <bufferAttribute
                  attach="attributes-position"
                  count={2}
                  array={new Float32Array([0, 0, 0, 3, 0, 0])}
                  itemSize={3}
                />
              </bufferGeometry>
              <lineBasicMaterial color={anomaly ? "#ff6600" : "#00ff88"} transparent opacity={0.5} />
            </line>
          </group>
        ))}
      </group>
    </>
  );
}

function DataPoints({ anomaly }) {
  const pointsRef = useRef();
  
  useFrame((state, delta) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.x += delta * 0.1;
      pointsRef.current.rotation.y += delta * 0.15;
    }
  });

  // Generate random data points in a sphere
  const dataPoints = Array.from({ length: 50 }, () => ({
    x: (Math.random() - 0.5) * 10,
    y: (Math.random() - 0.5) * 10,
    z: (Math.random() - 0.5) * 10,
  }));

  return (
    <group ref={pointsRef}>
      {dataPoints.map((point, i) => (
        <mesh key={i} position={[point.x, point.y, point.z]}>
          <sphereGeometry args={[0.08, 4, 4]} />
          <meshStandardMaterial 
            color={anomaly ? "#ff0088" : "#0088ff"} 
            emissive={anomaly ? "#ff0088" : "#0088ff"}
            emissiveIntensity={3}
          />
        </mesh>
      ))}
    </group>
  );
}

const TacticalMap = ({ anomaly = false }) => {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return (
      <div className="h-[500px] w-full bg-black/50 border border-aegis-primary/20 rounded-lg mt-6 flex items-center justify-center">
        <div className="text-aegis-muted">Loading 3D View...</div>
      </div>
    );
  }

  return (
    <div className="h-[500px] w-full bg-gradient-to-b from-black/70 to-black/50 border border-aegis-primary/40 rounded-lg mt-6 relative overflow-hidden shadow-[inset_0_0_30px_rgba(0,242,255,0.1),0_0_20px_rgba(0,0,0,0.8)]">
      {/* Header Info */}
      <div className="absolute top-4 left-4 z-10 font-mono pointer-events-none">
        <h3 className={`text-sm uppercase tracking-widest transition-all duration-500 font-bold ${
          anomaly ? 'text-red-500 animate-pulse' : 'text-aegis-primary'
        }`}>
          {anomaly ? "🔴 ANOMALY DETECTED" : "🟢 TACTICAL HOLODISPLAY"}
        </h3>
        <p className="text-[11px] text-aegis-muted mt-1 uppercase tracking-tighter">
          Vryndara Neural Network v3.2 • Real-time Visualization
        </p>
      </div>

      {/* Stats Panel */}
      <div className="absolute bottom-4 right-4 z-10 font-mono text-[10px] text-aegis-muted pointer-events-none bg-black/60 border border-aegis-primary/30 p-3 rounded">
        <div className="space-y-1">
          <p>FPS: 60</p>
          <p>Entities: 53</p>
          <p>Signal: {anomaly ? 'CRITICAL' : 'NOMINAL'}</p>
        </div>
      </div>

      {/* Instructions */}
      <div className="absolute bottom-4 left-4 z-10 font-mono text-[10px] text-aegis-muted pointer-events-none">
        <p className="bg-black/60 border border-aegis-primary/30 px-2 py-1 rounded">
          🖱️ Drag to rotate • Scroll to zoom
        </p>
      </div>

      {/* 3D Canvas */}
      <Canvas
        style={{ width: '100%', height: '100%' }}
        camera={{ position: [0, 5, 8], fov: 50 }}
      >
        {/* Lighting Setup */}
        <PerspectiveCamera makeDefault position={[0, 5, 8]} fov={50} />
        <OrbitControls 
          enablePan={true}
          enableZoom={true}
          maxDistance={20}
          minDistance={2}
          autoRotate={!anomaly}
          autoRotateSpeed={anomaly ? 3 : 0.5}
          dampingFactor={0.05}
        />

        {/* Ambients and Lights */}
        <ambientLight intensity={0.4} />
        <pointLight 
          position={[10, 10, 10]} 
          color={anomaly ? "#ff0044" : "#00f2ff"} 
          intensity={3}
          castShadow
        />
        <pointLight 
          position={[-10, -10, 10]} 
          color={anomaly ? "#ff6600" : "#0088ff"} 
          intensity={2}
        />
        <pointLight 
          position={[0, 0, -15]} 
          color={anomaly ? "#ff0044" : "#00ff88"} 
          intensity={1.5}
        />

        {/* Background Grid */}
        <Grid 
          infiniteGrid 
          fadeDistance={30}
          fadeStrength={1}
          cellColor={anomaly ? "#450a0a" : "#1e293b"} 
          sectionColor={anomaly ? "#ff0044" : "#0088ff"} 
          sectionThickness={2}
          cellSize={1}
          args={[10, 10]}
        />

        {/* Central Core System */}
        <RotatingCore anomaly={anomaly} />

        {/* Data Points Cloud */}
        <DataPoints anomaly={anomaly} />

        {/* Fog Effect */}
        <fog attach="fog" args={["#0b1120", 5, 30]} />
      </Canvas>

      {/* Scanline Overlay */}
      <div className="absolute inset-0 pointer-events-none opacity-5 bg-gradient-to-b from-transparent via-aegis-primary to-transparent animation-pulse"></div>
      
      {/* Corner Markers */}
      <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-aegis-primary/50"></div>
      <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-aegis-primary/50"></div>
      <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-aegis-primary/50"></div>
      <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-aegis-primary/50"></div>
    </div>
  );
};

export default TacticalMap;