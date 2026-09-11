import React from 'react';
import RealisticArchitectureAsset from './RealisticArchitectureAsset';

function Building({ position, size, color = '#d8d6ca', roof = '#334155', label }) {
  return (
    <group position={position}>
      <mesh position={[0, size[1] / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={size} />
        <meshStandardMaterial color={color} roughness={0.72} metalness={0.08} />
      </mesh>
      <mesh position={[0, size[1] + 0.3, 0]} rotation={[0, Math.PI / 4, 0]} castShadow>
        <boxGeometry args={[size[0] * 0.76, 0.6, size[2] * 0.76]} />
        <meshStandardMaterial color={roof} roughness={0.55} metalness={0.25} />
      </mesh>
      <mesh position={[0, size[1] * 0.42, size[2] / 2 + 0.02]}>
        <boxGeometry args={[Math.min(size[0] * 0.62, 8), Math.min(size[1] * 0.4, 2.2), 0.04]} />
        <meshStandardMaterial color="#17202b" roughness={0.3} metalness={0.35} />
      </mesh>
      {label && (
        <mesh position={[0, size[1] + 1.1, 0]}>
          <boxGeometry args={[Math.min(size[0] * 0.8, 12), 0.06, 0.06]} />
          <meshBasicMaterial color="#f8fafc" />
        </mesh>
      )}
    </group>
  );
}

function SolarRoof({ position, size }) {
  return (
    <group position={position}>
      {[...Array(6)].map((_, index) => (
        <mesh key={index} position={[(index - 2.5) * 1.5, 0.05, 0]} rotation={[-0.55, 0, 0]}>
          <boxGeometry args={[1.25, 0.04, size[2] * 0.65]} />
          <meshStandardMaterial color="#173c66" emissive="#0b5b8c" emissiveIntensity={0.2} metalness={0.8} roughness={0.18} />
        </mesh>
      ))}
    </group>
  );
}

function Field({ position, size, color = '#68884b', rows = 6 }) {
  return (
    <group position={position}>
      <mesh receiveShadow>
        <boxGeometry args={[size[0], 0.12, size[1]]} />
        <meshStandardMaterial color={color} roughness={1} />
      </mesh>
      {[...Array(rows)].map((_, index) => (
        <mesh key={index} position={[(index - (rows - 1) / 2) * (size[0] / rows), 0.09, 0]}>
          <boxGeometry args={[0.12, 0.04, size[1] * 0.86]} />
          <meshStandardMaterial color="#b3c779" roughness={1} />
        </mesh>
      ))}
    </group>
  );
}

function Road({ position, size, rotation = 0 }) {
  return (
    <mesh position={position} rotation={[-Math.PI / 2, 0, rotation]} receiveShadow>
      <planeGeometry args={size} />
      <meshStandardMaterial color="#626b6c" roughness={0.92} metalness={0.02} />
    </mesh>
  );
}

function WaterTank({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 1.4, 0]} castShadow>
        <cylinderGeometry args={[1.7, 1.7, 2.8, 24]} />
        <meshStandardMaterial color="#6ca3b9" roughness={0.3} metalness={0.4} />
      </mesh>
      <mesh position={[0, 2.95, 0]}>
        <cylinderGeometry args={[1.82, 1.82, 0.2, 24]} />
        <meshStandardMaterial color="#dbeafe" roughness={0.25} metalness={0.4} />
      </mesh>
    </group>
  );
}

export default function EstateMasterLayout() {
  return (
    <group>
      <mesh position={[0, -0.08, 0]} receiveShadow>
        <boxGeometry args={[135, 0.12, 90]} />
        <meshStandardMaterial color="#587451" roughness={1} />
      </mesh>
      <mesh position={[0, 0.1, -44.5]}>
        <boxGeometry args={[135, 0.35, 0.35]} />
        <meshStandardMaterial color="#26382d" roughness={0.8} />
      </mesh>
      <mesh position={[0, 0.1, 44.5]}>
        <boxGeometry args={[135, 0.35, 0.35]} />
        <meshStandardMaterial color="#26382d" roughness={0.8} />
      </mesh>
      <mesh position={[-67.25, 0.1, 0]}>
        <boxGeometry args={[0.35, 0.35, 90]} />
        <meshStandardMaterial color="#26382d" roughness={0.8} />
      </mesh>
      <mesh position={[67.25, 0.1, 0]}>
        <boxGeometry args={[0.35, 0.35, 90]} />
        <meshStandardMaterial color="#26382d" roughness={0.8} />
      </mesh>

      <Road position={[0, 0.02, 0]} size={[135, 6]} />
      <Road position={[-25, 0.03, -20]} size={[6, 42]} />
      <Road position={[30, 0.03, 18]} size={[6, 50]} />

      <Field position={[-37, 0.14, -31]} size={[42, 22]} color="#66884b" />
      <Field position={[18, 0.14, -31]} size={[46, 18]} color="#6f934f" rows={8} />
      <Field position={[31, 0.14, 13]} size={[36, 28]} color="#a2a35b" rows={8} />
      <Field position={[-8, 0.14, 28]} size={[28, 16]} color="#78934e" rows={5} />

      <RealisticArchitectureAsset position={[-35, 0.15, 6]} scale={0.62} />
      <SolarRoof position={[-35, 8.4, 6]} size={[33, 21]} />
      <Building position={[18, 0.15, 28]} size={[30, 5, 18]} color="#d7d3c6" roof="#475569" label />
      <SolarRoof position={[18, 5.4, 28]} size={[30, 18]} />
      <Building position={[45, 0.15, 5]} size={[18, 6, 14]} color="#c6c9c4" roof="#334155" label />
      <SolarRoof position={[45, 6.4, 5]} size={[18, 14]} />

      <WaterTank position={[-5, 0, 7]} />
      <WaterTank position={[2, 0, 7]} />
      <mesh position={[8, 0.25, 7]} receiveShadow>
        <cylinderGeometry args={[1.8, 1.8, 0.18, 32]} />
        <meshStandardMaterial color="#275d9a" roughness={0.25} metalness={0.1} />
      </mesh>

      <group position={[0, 0.2, 38]}>
        <mesh>
          <boxGeometry args={[38, 0.18, 10]} />
          <meshStandardMaterial color="#c6b58c" roughness={1} />
        </mesh>
        {[...Array(9)].map((_, index) => (
          <mesh key={index} position={[(index - 4) * 3.8, 0.2, 0]}>
            <boxGeometry args={[0.18, 0.4, 8]} />
            <meshStandardMaterial color="#415a43" roughness={0.95} />
          </mesh>
        ))}
      </group>
    </group>
  );
}
