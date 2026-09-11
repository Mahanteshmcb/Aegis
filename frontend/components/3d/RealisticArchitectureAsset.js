import React, { useMemo } from 'react';
import { Box3, Vector3 } from 'three';
import { useGLTF } from '@react-three/drei';

const FACTORY_URL = '/assets/polyhaven/modular_factory_facade/modular_factory_facade.gltf';

function normalize(scene) {
  const clone = scene.clone(true);
  const bounds = new Box3().setFromObject(clone);
  const center = bounds.getCenter(new Vector3());
  clone.position.set(-center.x, -bounds.min.y, -center.z);
  return clone;
}

export default function RealisticArchitectureAsset({ position = [0, 0, 0], scale = 0.62 }) {
  const { scene } = useGLTF(FACTORY_URL);
  const model = useMemo(() => normalize(scene), [scene]);
  return <primitive object={model} position={position} scale={scale} castShadow receiveShadow />;
}

useGLTF.preload(FACTORY_URL);
