import React, { useRef, useEffect, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

/**
 * Animated 3D Background Component
 * Renders floating particles, orbs, and geometric shapes
 */
function FloatingOrb({ position, color, speed }) {
  const meshRef = useRef();
  const time = useRef(0);

  useFrame(() => {
    time.current += speed * 0.016;
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(time.current) * 5;
      meshRef.current.rotation.x += 0.003;
      meshRef.current.rotation.y += 0.005;
    }
  });

  return (
    <mesh ref={meshRef} position={position}>
      <icosahedronGeometry args={[2, 4]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.5}
        metalness={0.8}
        roughness={0.2}
        wireframe
      />
    </mesh>
  );
}

/**
 * Background3D - Main component
 */
export default function Background3D({ children, glowColor = '#00f2ff' }) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) return <div className="relative w-full h-full">{children}</div>;

  return (
    <div className="relative w-full h-full overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-black">
      {/* 3D Canvas Background */}
      <div className="absolute inset-0 z-0">
        <Canvas
          camera={{ position: [0, 0, 50], fov: 60 }}
          style={{ width: '100%', height: '100%' }}
          gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
          onCreated={(state) => state.gl.setPixelRatio(Math.min(window.devicePixelRatio, 2))}
        >
          <ambientLight intensity={0.3} />
          <pointLight position={[20, 20, 20]} intensity={0.5} color={glowColor} />

          <FloatingOrb position={[-20, 0, -30]} color="#00f2ff" speed={0.3} />
          <FloatingOrb position={[20, 15, -30]} color="#ff00ff" speed={0.4} />
          <FloatingOrb position={[0, -20, -30]} color="#00ff88" speed={0.35} />
        </Canvas>
      </div>

      {/* Gradient Overlay */}
      <div className="absolute inset-0 z-[1] pointer-events-none bg-gradient-to-b from-transparent via-slate-950/20 to-slate-950/80" />

      {/* Content Container */}
      <div className="relative z-[2] w-full h-full">{children}</div>
    </div>
  );
}
