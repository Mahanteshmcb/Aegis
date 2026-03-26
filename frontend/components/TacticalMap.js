import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Grid, PerspectiveCamera, Float } from '@react-three/drei';

function RotatingCore({ anomaly }) {
  const meshRef = useRef();
  
  // Rotate the central "Aegis Core" slowly
  useFrame((state, delta) => {
    // Spin faster if there's an anomaly
    const speed = anomaly ? 3.0 : 0.5;
    meshRef.current.rotation.y += delta * speed;
    meshRef.current.rotation.z += delta * (speed / 2);
  });

  return (
    <Float speed={anomaly ? 5 : 1.5} rotationIntensity={2} floatIntensity={2}>
      <mesh ref={meshRef}>
        <octahedronGeometry args={[1, 0]} />
        <meshStandardMaterial 
          color={anomaly ? "#ff0044" : "#00f2ff"} 
          wireframe 
          emissive={anomaly ? "#ff0044" : "#00f2ff"} 
          emissiveIntensity={anomaly ? 10 : 2} 
        />
      </mesh>
    </Float>
  );
}

const TacticalMap = ({ anomaly }) => {
  return (
    <div className="h-[400px] w-full bg-black/50 border border-aegis-primary/20 rounded-lg mt-6 relative overflow-hidden shadow-[inset_0_0_20px_rgba(0,0,0,0.8)]">
      <div className="absolute top-4 left-4 z-10 font-mono">
        <h3 className={`text-xs uppercase tracking-widest transition-colors duration-500 ${
          anomaly ? 'text-red-500 font-bold' : 'text-aegis-primary'
        }`}>
          {anomaly ? "!! CRITICAL ANOMALY DETECTED // SECTOR ALPHA" : "Holographic Tactical View // System Nominal"}
        </h3>
        <p className="text-[10px] text-aegis-muted mt-1 uppercase tracking-tighter">
          Vryndara Kernel v3.1 // Neural Stream Active
        </p>
      </div>
      
      <Canvas>
        <PerspectiveCamera makeDefault position={[5, 5, 5]} />
        <OrbitControls 
          enablePan={false} 
          maxDistance={12} 
          minDistance={3} 
          autoRotate={!anomaly} 
          autoRotateSpeed={0.5}
        />
        
        {/* Environment Lighting */}
        <ambientLight intensity={0.2} />
        <pointLight position={[10, 10, 10]} color={anomaly ? "#ff0044" : "#00f2ff"} intensity={2} />
        
        {/* Cyber Grid Base */}
        <Grid 
          infiniteGrid 
          fadeDistance={25} 
          cellColor={anomaly ? "#450a0a" : "#1e293b"} 
          sectionColor={anomaly ? "#ff0044" : "#00f2ff"} 
          sectionThickness={1.5} 
          cellSize={1}
        />
        
        {/* Central Intelligence Core */}
        <RotatingCore anomaly={anomaly} />
      </Canvas>
      
      {/* Scanning Line Overlay Effect */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-aegis-primary/5 to-transparent h-2 w-full animate-scan"></div>
    </div>
  );
};

export default TacticalMap;